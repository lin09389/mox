"""大模型接口抽象层"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import Enum

from openai import AsyncOpenAI

try:
    from openai import AsyncAzureOpenAI
except ImportError:
    AsyncAzureOpenAI = None
from anthropic import AsyncAnthropic

try:
    import google.genai as genai
    from google.genai import types

    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False

from mox.infrastructure.config import settings


class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MINIMAX = "minimax"
    GOOGLE = "google"
    LOCAL = "local"
    DEEPSEEK = "deepseek"
    COHERE = "cohere"
    GROQ = "groq"
    AZURE = "azure"
    QWEN = "qwen"
    ERNIE = "ernie"
    ZHIPU = "zhipu"
    HUGGINGFACE = "huggingface"


@dataclass
class Message:
    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    raw_response: Optional[Any] = None


class BaseLLM(ABC):
    """大模型基类"""

    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 2048, **kwargs):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """流式生成，返回异步迭代器"""
        yield ""
        raise NotImplementedError

    def _build_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        return [msg.to_dict() for msg in messages]


class OpenAILLM(BaseLLM):
    """OpenAI 模型接口"""

    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None, **kwargs):
        super().__init__(model, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self._build_messages(messages),
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                finish_reason=response.choices[0].finish_reason or "stop",
                raw_response=response,
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(messages),
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicLLM(BaseLLM):
    """Anthropic Claude 模型接口"""

    def __init__(
        self, model: str = "claude-3-opus-20240229", api_key: Optional[str] = None, **kwargs
    ):
        super().__init__(model, **kwargs)
        self.client = AsyncAnthropic(api_key=api_key or settings.ANTHROPIC_API_KEY)

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        system_prompt = None
        chat_messages = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                chat_messages.append(msg.to_dict())

        response = await self.client.messages.create(
            model=self.model,
            messages=chat_messages,
            system=system_prompt,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        )

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
            raw_response=response,
        )

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        system_prompt = None
        chat_messages = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                chat_messages.append(msg.to_dict())

        async with self.client.messages.stream(
            model=self.model,
            messages=chat_messages,
            system=system_prompt,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        ) as stream:
            async for text in stream.text_stream:
                yield text


class MiniMaxLLM(BaseLLM):
    """MiniMax 模型接口

    MiniMax API 兼容 OpenAI 格式
    文档: https://www.minimaxi.com/document/
    """

    def __init__(
        self,
        model: str = "abab2.5-chat",
        api_key: Optional[str] = None,
        group_id: Optional[str] = None,
        base_url: str = "https://api.minimax.chat/v1",
        **kwargs,
    ):
        super().__init__(model, **kwargs)
        self.group_id = group_id
        self.base_url = base_url
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        client = self._get_client()

        response = await client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(messages),
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=response.choices[0].finish_reason or "stop",
            raw_response=response,
        )

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        client = self._get_client()

        stream = await client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(messages),
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class OllamaLLM(BaseLLM):
    """Ollama 本地模型接口 (兼容 OpenAI API)"""

    def __init__(
        self,
        model: str = "llama3",
        api_key: str = "ollama",
        base_url: str = "http://localhost:11434/v1",
        **kwargs,
    ):
        super().__init__(model, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self._build_messages(messages),
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                finish_reason=response.choices[0].finish_reason or "stop",
                raw_response=response,
            )
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {str(e)}") from e

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(messages),
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class HuggingFaceLLM(BaseLLM):
    """HuggingFace Transformers 本地模型接口

    直接加载 transformers 格式的本地模型或 HuggingFace Hub 模型，
    支持 PEFT/LoRA 适配器、4-bit/8-bit 量化、多 GPU 加载。
    """

    def __init__(
        self,
        model: str = "gpt2",
        adapter_path: Optional[str] = None,
        device_map: str = "auto",
        torch_dtype: str = "bfloat16",
        load_in_4bit: bool = False,
        load_in_8bit: bool = False,
        trust_remote_code: bool = False,
        **kwargs,
    ):
        super().__init__(model, **kwargs)
        self.model_name_or_path = model
        self.adapter_path = adapter_path
        self.device_map = device_map
        self.load_in_4bit = load_in_4bit
        self.load_in_8bit = load_in_8bit
        self.trust_remote_code = trust_remote_code

        # Parse torch_dtype
        dtype_map = {
            "float32": "float32",
            "float16": "float16",
            "bfloat16": "bfloat16",
            "bf16": "bfloat16",
            "fp16": "float16",
            "fp32": "float32",
        }
        self.torch_dtype_str = dtype_map.get(torch_dtype.lower(), "bfloat16")

        self._model = None
        self._tokenizer = None
        self._device = None

        self._init_model()

    def _init_model(self):
        """初始化模型和 tokenizer"""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError:
            raise ImportError(
                "transformers and torch are required for HuggingFaceLLM. "
                "Install with: pip install transformers torch"
            )

        dtype_map = {
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }
        torch_dtype = dtype_map.get(self.torch_dtype_str, torch.bfloat16)

        # Build load kwargs
        load_kwargs = {
            "torch_dtype": torch_dtype,
            "trust_remote_code": self.trust_remote_code,
        }

        if self.device_map != "cpu":
            load_kwargs["device_map"] = self.device_map

        # Quantization config
        if self.load_in_4bit or self.load_in_8bit:
            try:
                from transformers import BitsAndBytesConfig

                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=self.load_in_4bit,
                    load_in_8bit=self.load_in_8bit,
                    bnb_4bit_compute_dtype=torch_dtype,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
                load_kwargs["quantization_config"] = bnb_config
            except ImportError:
                raise ImportError(
                    "bitsandbytes is required for quantization. "
                    "Install with: pip install bitsandbytes"
                )

        # Load model
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name_or_path,
            **load_kwargs,
        )

        # Load LoRA adapter if specified
        if self.adapter_path:
            try:
                from peft import PeftModel

                self._model = PeftModel.from_pretrained(
                    self._model,
                    self.adapter_path,
                )
            except ImportError:
                raise ImportError(
                    "peft is required for LoRA adapter loading. "
                    "Install with: pip install peft"
                )

        # Load tokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_name_or_path,
            trust_remote_code=self.trust_remote_code,
        )
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        # Determine device
        if hasattr(self._model, "device"):
            self._device = str(self._model.device)
        elif self.device_map == "cpu":
            self._device = "cpu"
        else:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            if self.device_map == "cpu":
                self._model = self._model.to(self._device)

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        if self._model is None or self._tokenizer is None:
            raise RuntimeError("Model not initialized")

        import torch

        # Build prompt from messages
        prompt = self._build_prompt(messages)

        inputs = self._tokenizer(prompt, return_tensors="pt")
        if self._device and self._device != "cpu":
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

        gen_kwargs = {
            "max_new_tokens": max_tokens or self.max_tokens,
            "do_sample": True,
            "temperature": temperature or self.temperature,
            "pad_token_id": self._tokenizer.pad_token_id,
            "eos_token_id": self._tokenizer.eos_token_id,
        }

        with torch.no_grad():
            outputs = self._model.generate(**inputs, **gen_kwargs)

        generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        content = self._tokenizer.decode(generated_tokens, skip_special_tokens=True)

        return LLMResponse(
            content=content,
            model=self.model,
            usage={
                "prompt_tokens": inputs["input_ids"].shape[1],
                "completion_tokens": len(generated_tokens),
                "total_tokens": inputs["input_ids"].shape[1] + len(generated_tokens),
            },
            finish_reason="stop",
            raw_response=None,
        )

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        if self._model is None or self._tokenizer is None:
            raise RuntimeError("Model not initialized")

        import torch

        prompt = self._build_prompt(messages)
        inputs = self._tokenizer(prompt, return_tensors="pt")
        if self._device and self._device != "cpu":
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

        gen_kwargs = {
            "max_new_tokens": max_tokens or self.max_tokens,
            "do_sample": True,
            "temperature": temperature or self.temperature,
            "pad_token_id": self._tokenizer.pad_token_id,
            "eos_token_id": self._tokenizer.eos_token_id,
        }

        with torch.no_grad():
            outputs = self._model.generate(**inputs, **gen_kwargs)

        generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]

        # Stream token by token
        for i in range(1, len(generated_tokens) + 1):
            chunk = self._tokenizer.decode(generated_tokens[:i], skip_special_tokens=True)
            prev_chunk = self._tokenizer.decode(generated_tokens[:i - 1], skip_special_tokens=True) if i > 1 else ""
            yield chunk[len(prev_chunk):]

    def _build_prompt(self, messages: List[Message]) -> str:
        """将消息列表转换为模型输入 prompt"""
        parts = []
        for msg in messages:
            if msg.role == "system":
                parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                parts.append(f"Assistant: {msg.content}")
        return "\n\n".join(parts) + "\n\nAssistant:"

    @property
    def model_instance(self):
        """返回底层 transformers 模型实例，供白盒攻击使用"""
        return self._model

    @property
    def tokenizer_instance(self):
        """返回 tokenizer 实例，供白盒攻击使用"""
        return self._tokenizer


class GeminiLLM(BaseLLM):
    """Google Gemini 模型接口"""

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        api_key: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(model, **kwargs)
        if not GOOGLE_GENAI_AVAILABLE:
            raise ImportError("google-genai is required. Install with: pip install google-genai")
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        client = self._get_client()

        contents, system_instruction = self._build_contents(messages)

        config_kwargs = {
            "temperature": temperature or self.temperature,
            "max_output_tokens": max_tokens or self.max_tokens,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        response = await client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        return LLMResponse(
            content=response.text,
            model=self.model,
            usage={
                "prompt_tokens": getattr(response, "prompt_token_count", 0),
                "completion_tokens": getattr(response, "candidates_token_count", 0),
                "total_tokens": getattr(response, "total_token_count", 0),
            },
            finish_reason="stop",
            raw_response=response,
        )

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        client = self._get_client()

        contents, system_instruction = self._build_contents(messages)

        config_kwargs = {
            "temperature": temperature or self.temperature,
            "max_output_tokens": max_tokens or self.max_tokens,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        async for chunk in await client.aio.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs),
        ):
            if chunk.text:
                yield chunk.text

    def _build_contents(self, messages: List[Message]) -> tuple:
        """构建 Gemini 格式的 contents 和 system_instruction

        修复: Gemini API 不支持在 contents 中传递 system 角色，
        需要通过 system_instruction 参数单独传递。
        返回 (contents, system_instruction) 元组。
        """
        contents = []
        system_instruction = None
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                contents.append(types.Content(role="user", parts=[types.Part(text=msg.content)]))
            elif msg.role == "model":
                contents.append(types.Content(role="model", parts=[types.Part(text=msg.content)]))
        return contents, system_instruction


class DeepSeekLLM(BaseLLM):
    """DeepSeek 模型接口 (兼容 OpenAI API)"""

    def __init__(
        self,
        model: str = "deepseek-chat",
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com/v1",
        **kwargs,
    ):
        super().__init__(model, **kwargs)
        self.base_url = base_url
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        client = self._get_client()

        response = await client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(messages),
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=response.choices[0].finish_reason or "stop",
            raw_response=response,
        )

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        client = self._get_client()

        stream = await client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(messages),
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class CohereLLM(BaseLLM):
    """Cohere 模型接口"""

    def __init__(
        self,
        model: str = "command-r-plus",
        api_key: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import cohere

                self._client = cohere.AsyncClient(self.api_key)
            except ImportError:
                raise ImportError("cohere package required. Install with: pip install cohere")
        return self._client

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        client = self._get_client()

        chat_history = []
        for msg in messages[:-1]:
            chat_history.append(
                {"role": msg.role if msg.role != "system" else "system", "message": msg.content}
            )
        last_message = messages[-1].content if messages else ""

        response = await client.chat(
            model=self.model,
            message=last_message,
            chat_history=chat_history,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        )

        return LLMResponse(
            content=response.text,
            model=self.model,
            usage={
                "prompt_tokens": response.meta.tokens.input_tokens
                if hasattr(response, "meta") and hasattr(response.meta, "tokens")
                else 0,
                "completion_tokens": response.meta.tokens.output_tokens
                if hasattr(response, "meta") and hasattr(response.meta, "tokens")
                else 0,
                "total_tokens": (
                    response.meta.tokens.input_tokens + response.meta.tokens.output_tokens
                )
                if hasattr(response, "meta") and hasattr(response.meta, "tokens")
                else 0,
            },
            finish_reason="stop",
            raw_response=response,
        )

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        client = self._get_client()

        chat_history = []
        for msg in messages[:-1]:
            chat_history.append(
                {"role": msg.role if msg.role != "system" else "system", "message": msg.content}
            )
        last_message = messages[-1].content if messages else ""

        async for event in client.chat_stream(
            model=self.model,
            message=last_message,
            chat_history=chat_history,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        ):
            if event.text:
                yield event.text


class GroqLLM(BaseLLM):
    """Groq 模型接口 (高吞吐量推理)"""

    def __init__(
        self,
        model: str = "llama-3.1-70b-versatile",
        api_key: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(model, **kwargs)
        self.base_url = "https://api.groq.com/openai/v1"
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        client = self._get_client()

        response = await client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(messages),
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=response.choices[0].finish_reason or "stop",
            raw_response=response,
        )

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        client = self._get_client()

        stream = await client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(messages),
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AzureOpenAILLM(BaseLLM):
    """Azure OpenAI 模型接口"""

    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        api_version: str = "2024-02-01",
        **kwargs,
    ):
        super().__init__(model, **kwargs)
        self.azure_endpoint = azure_endpoint
        self.api_version = api_version
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            if AsyncAzureOpenAI is None:
                raise RuntimeError(
                    "Azure OpenAI client not available. Please install azure-openai package: pip install azure-openai"
                )
            self._client = AsyncAzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.azure_endpoint,
                api_version=self.api_version,
            )
        return self._client

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        client = self._get_client()

        response = await client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(messages),
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=response.choices[0].finish_reason or "stop",
            raw_response=response,
        )

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        client = self._get_client()

        stream = await client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(messages),
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class LLMFactory:
    """LLM 工厂类"""

    LOCAL_MODELS = {
        "llama3",
        "llama3.1",
        "llama3.2",
        "llama2",
        "llama",
        "qwen",
        "qwen2",
        "qwen2.5",
        "qwen2.5-coder",
        "qwen3",
        "qwen3:4b",
        "gemma",
        "gemma2",
        "gemma3",
        "gemma3:4b",
        "mistral",
        "mixtral",
        "phi",
        "phi3",
        "codellama",
        "deepseek",
        "deepseek-coder",
        "command-r",
        "falcon",
    }

    @staticmethod
    def create(provider: ModelProvider, model: Optional[str] = None, **kwargs) -> BaseLLM:
        if provider == ModelProvider.OPENAI:
            return OpenAILLM(model=model or "gpt-4o", **kwargs)
        elif provider == ModelProvider.ANTHROPIC:
            return AnthropicLLM(model=model or "claude-sonnet-4-20250514", **kwargs)
        elif provider == ModelProvider.MINIMAX:
            return MiniMaxLLM(model=model or "abab2.5-chat", **kwargs)
        elif provider == ModelProvider.GOOGLE:
            return GeminiLLM(model=model or "gemini-2.0-flash", **kwargs)
        elif provider == ModelProvider.LOCAL:
            return OllamaLLM(
                model=model or "qwen3:4b",
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                **kwargs,
            )
        elif provider == ModelProvider.DEEPSEEK:
            return DeepSeekLLM(model=model or "deepseek-chat", **kwargs)
        elif provider == ModelProvider.COHERE:
            return CohereLLM(model=model or "command-r-plus", **kwargs)
        elif provider == ModelProvider.GROQ:
            return GroqLLM(model=model or "llama-3.1-70b-versatile", **kwargs)
        elif provider == ModelProvider.AZURE:
            return AzureOpenAILLM(model=model or "gpt-4", **kwargs)
        elif provider == ModelProvider.HUGGINGFACE:
            return HuggingFaceLLM(
                model=model or "gpt2",
                device_map=kwargs.pop("device_map", settings.DEVICE_MAP),
                torch_dtype=kwargs.pop("torch_dtype", settings.TORCH_DTYPE),
                load_in_4bit=kwargs.pop("load_in_4bit", settings.LOAD_IN_4BIT),
                load_in_8bit=kwargs.pop("load_in_8bit", settings.LOAD_IN_8BIT),
                adapter_path=kwargs.pop("adapter_path", settings.LORA_ADAPTER_PATH),
                **kwargs,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def create_from_model_name(model: str, **kwargs) -> BaseLLM:
        model_lower = model.lower()
        base_url = kwargs.get("base_url", "")
        provider = kwargs.get("provider", "")

        # Explicit provider override
        if provider:
            provider_map = {
                "openai": ModelProvider.OPENAI,
                "anthropic": ModelProvider.ANTHROPIC,
                "minimax": ModelProvider.MINIMAX,
                "google": ModelProvider.GOOGLE,
                "local": ModelProvider.LOCAL,
                "ollama": ModelProvider.LOCAL,
                "deepseek": ModelProvider.DEEPSEEK,
                "cohere": ModelProvider.COHERE,
                "groq": ModelProvider.GROQ,
                "azure": ModelProvider.AZURE,
                "huggingface": ModelProvider.HUGGINGFACE,
                "hf": ModelProvider.HUGGINGFACE,
            }
            p = provider_map.get(provider.lower())
            if p:
                kwargs.pop("provider", None)
                return LLMFactory.create(p, model=model, **kwargs)

        # 优先检查 base_url - 如果是本地 Ollama 服务，直接返回 OllamaLLM
        if base_url and (
            "localhost" in base_url or "11434" in base_url or "ollama" in base_url.lower()
        ):
            base_url_arg = kwargs.pop("base_url", "http://localhost:11434/v1")
            api_key = kwargs.pop("api_key", "ollama")
            return OllamaLLM(model=model, base_url=base_url_arg, api_key=api_key, **kwargs)

        # HuggingFace model name format: "org/model-name" or local path
        if "/" in model or model.startswith(".") or model.startswith("/") or model.startswith("~"):
            import os

            is_local_path = os.path.exists(os.path.expanduser(model))
            if "/" in model or is_local_path:
                return HuggingFaceLLM(
                    model=model,
                    device_map=kwargs.pop("device_map", settings.DEVICE_MAP),
                    torch_dtype=kwargs.pop("torch_dtype", settings.TORCH_DTYPE),
                    load_in_4bit=kwargs.pop("load_in_4bit", settings.LOAD_IN_4BIT),
                    load_in_8bit=kwargs.pop("load_in_8bit", settings.LOAD_IN_8BIT),
                    adapter_path=kwargs.pop("adapter_path", settings.LORA_ADAPTER_PATH),
                    **kwargs,
                )

        # OpenAI models (gpt-4, gpt-3.5, o1, o3)
        if (
            model_lower.startswith("gpt")
            or model_lower.startswith("o1")
            or model_lower.startswith("o3")
        ):
            return OpenAILLM(model=model, **kwargs)
        # Anthropic models
        elif model_lower.startswith("claude"):
            return AnthropicLLM(model=model, **kwargs)
        # Google Gemini models
        elif model_lower.startswith("gemini"):
            return GeminiLLM(model=model, **kwargs)
        # MiniMax models
        elif model_lower.startswith("abab") or model_lower.startswith("minimax"):
            return MiniMaxLLM(model=model, **kwargs)
        # DeepSeek models
        elif model_lower.startswith("deepseek"):
            return DeepSeekLLM(model=model, **kwargs)
        # Cohere models
        elif model_lower.startswith("command"):
            return CohereLLM(model=model, **kwargs)
        # Azure OpenAI - check base_url first as it's more specific
        elif "azure" in kwargs.get("base_url", "").lower() or "-azure" in model_lower:
            return AzureOpenAILLM(model=model, **kwargs)
        # Local/Ollama models - check exact matches first (before Groq)
        elif model_lower in LLMFactory.LOCAL_MODELS or any(
            model_lower.startswith(m) for m in LLMFactory.LOCAL_MODELS
        ):
            base_url_arg = kwargs.pop("base_url", "http://localhost:11434/v1")
            api_key = kwargs.pop("api_key", "ollama")
            return OllamaLLM(model=model, base_url=base_url_arg, api_key=api_key, **kwargs)
        # Groq models - mixtral, llama-3*, qwen (when using Groq API)
        elif (
            model_lower.startswith("mixtral")
            or model_lower.startswith("llama-3")
            or model_lower.startswith("qwen")
        ):
            return GroqLLM(model=model, **kwargs)
        else:
            # Default to HuggingFace for unknown models instead of raising error
            return HuggingFaceLLM(
                model=model,
                device_map=kwargs.pop("device_map", settings.DEVICE_MAP),
                torch_dtype=kwargs.pop("torch_dtype", settings.TORCH_DTYPE),
                load_in_4bit=kwargs.pop("load_in_4bit", settings.LOAD_IN_4BIT),
                load_in_8bit=kwargs.pop("load_in_8bit", settings.LOAD_IN_8BIT),
                adapter_path=kwargs.pop("adapter_path", settings.LORA_ADAPTER_PATH),
                **kwargs,
            )
