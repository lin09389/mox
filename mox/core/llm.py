"""大模型接口抽象层"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
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

from .config import settings


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


@dataclass
class Message:
    """支持纯文本或多模态 content parts（OpenAI vision 格式）"""

    role: str
    content: Union[str, List[Dict[str, Any]]]

    def to_dict(self) -> Dict[str, Any]:
        return {"role": self.role, "content": self.content}

    @classmethod
    def text(cls, role: str, text: str) -> "Message":
        return cls(role=role, content=text)

    @classmethod
    def with_image(
        cls,
        role: str,
        text: str,
        image_url: str,
        detail: str = "auto",
    ) -> "Message":
        return cls(
            role=role,
            content=[
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": {"url": image_url, "detail": detail}},
            ],
        )

    @property
    def is_multimodal(self) -> bool:
        return isinstance(self.content, list)


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

        contents = self._build_contents(messages)

        response = await client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=temperature or self.temperature,
                max_output_tokens=max_tokens or self.max_tokens,
            ),
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

        contents = self._build_contents(messages)

        async for chunk in await client.aio.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=temperature or self.temperature,
                max_output_tokens=max_tokens or self.max_tokens,
            ),
        ):
            if chunk.text:
                yield chunk.text

    def _build_contents(self, messages: List[Message]) -> List[Any]:
        contents = []
        for msg in messages:
            if msg.role == "user":
                contents.append(types.Content(role="user", parts=[types.Part(text=msg.content)]))
            elif msg.role == "model":
                contents.append(types.Content(role="model", parts=[types.Part(text=msg.content)]))
        return contents


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

        chat_messages = [{"role": msg.role, "message": msg.content} for msg in messages]

        response = await client.chat(
            model=self.model,
            message=chat_messages[0]["message"] if chat_messages else "",
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        )

        return LLMResponse(
            content=response.text,
            model=self.model,
            usage={
                "prompt_tokens": response.token_count if hasattr(response, "token_count") else 0,
                "completion_tokens": 0,
                "total_tokens": response.token_count if hasattr(response, "token_count") else 0,
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

        chat_messages = [{"role": msg.role, "message": msg.content} for msg in messages]

        async for event in client.chat_stream(
            model=self.model,
            message=chat_messages[0]["message"] if chat_messages else "",
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
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def create_from_model_name(model: str, **kwargs) -> BaseLLM:
        model_lower = model.lower()
        base_url = kwargs.get("base_url", "")

        # 优先检查 base_url - 如果是本地 Ollama 服务，直接返回 OllamaLLM
        if base_url and (
            "localhost" in base_url or "11434" in base_url or "ollama" in base_url.lower()
        ):
            base_url_arg = kwargs.pop("base_url", "http://localhost:11434/v1")
            api_key = kwargs.pop("api_key", "ollama")
            return OllamaLLM(model=model, base_url=base_url_arg, api_key=api_key, **kwargs)

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
            raise ValueError(
                f"Unknown model: {model}. Please specify the provider explicitly using LLMFactory.create(provider, model)."
            )
