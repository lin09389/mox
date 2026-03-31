"""国产模型支持 - 通义千问、文心一言、智谱AI"""

import json
from typing import List, Optional
from dataclasses import dataclass

import aiohttp

from mox.core.llm import BaseLLM, LLMResponse, Message, ModelProvider
from mox.core.logging import get_logger

logger = get_logger("chinese_llm")


@dataclass
class QwenConfig:
    """通义千问配置"""

    api_key: str
    model: str = "qwen-turbo"
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"


@dataclass
class ErnieConfig:
    """文心一言配置"""

    api_key: str
    secret_key: str
    model: str = "ernie-4.0-8k"
    base_url: str = "https://qianfan.baidubce.com/v2"


@dataclass
class ZhipuConfig:
    """智谱AI配置"""

    api_key: str
    model: str = "glm-4"
    base_url: str = "https://open.bigmodel.cn/api/paas/v4"


class QwenLLM(BaseLLM):
    """通义千问 LLM"""

    provider = ModelProvider.QWEN

    def __init__(self, config: QwenConfig):
        super().__init__(model=config.model, api_key=config.api_key)
        self.config = config
        self.base_url = config.base_url

    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        """生成回复"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.config.model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "top_p": kwargs.get("top_p", 0.9),
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"Qwen API error: {error}")

                result = await resp.json()
                content = result["choices"][0]["message"]["content"]

                return LLMResponse(
                    content=content,
                    model=self.config.model,
                    usage=result.get("usage", {}),
                )

    async def generate_stream(self, messages: List[Message], **kwargs):
        """流式生成"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.config.model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as resp:
                async for line in resp.content:
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    content = (
                                        chunk["choices"][0].get("delta", {}).get("content", "")
                                    )
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                pass


class ErnieLLM(BaseLLM):
    """文心一言 LLM"""

    provider = ModelProvider.ERNIE

    def __init__(self, config: ErnieConfig):
        super().__init__(model=config.model, api_key=config.api_key)
        self.config = config
        self._access_token: Optional[str] = None
        self._token_expires_at = 0

    async def _get_access_token(self) -> str:
        """获取访问令牌"""
        import time

        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        auth_url = "https://qianfan.baidubce.com/oauth/2.0/token"
        auth_payload = {
            "grant_type": "client_credentials",
            "client_id": self.config.api_key,
            "client_secret": self.config.secret_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, data=auth_payload) as resp:
                result = await resp.json()
                self._access_token = result["access_token"]
                self._token_expires_at = time.time() + result.get("expires_in", 2592000)
                return self._access_token

    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        """生成回复"""
        access_token = await self._get_access_token()

        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.config.model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_output_tokens": kwargs.get("max_tokens", 2048),
            "top_p": kwargs.get("top_p", 0.9),
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.config.base_url}/chat/completions?access_token={access_token}",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"Ernie API error: {error}")

                result = await resp.json()
                content = result["choices"][0]["message"]["content"]

                return LLMResponse(
                    content=content,
                    model=self.config.model,
                    usage=result.get("usage", {}),
                )

    async def generate_stream(self, messages: List[Message], **kwargs):
        """流式生成"""
        access_token = await self._get_access_token()

        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.config.model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_output_tokens": kwargs.get("max_tokens", 2048),
            "stream": True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.config.base_url}/chat/completions?access_token={access_token}",
                headers=headers,
                json=payload,
            ) as resp:
                async for line in resp.content:
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    content = (
                                        chunk["choices"][0].get("delta", {}).get("content", "")
                                    )
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                pass


class ZhipuLLM(BaseLLM):
    """智谱AI LLM"""

    provider = ModelProvider.ZHIPU

    def __init__(self, config: ZhipuConfig):
        super().__init__(model=config.model, api_key=config.api_key)
        self.config = config
        self.base_url = config.base_url

    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        """生成回复"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.config.model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "top_p": kwargs.get("top_p", 0.9),
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"Zhipu API error: {error}")

                result = await resp.json()
                content = result["choices"][0]["message"]["content"]

                return LLMResponse(
                    content=content,
                    model=self.config.model,
                    usage=result.get("usage", {}),
                )

    async def generate_stream(self, messages: List[Message], **kwargs):
        """流式生成"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.config.model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as resp:
                async for line in resp.content:
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    content = (
                                        chunk["choices"][0].get("delta", {}).get("content", "")
                                    )
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                pass


def create_qwen_llm(api_key: str, model: str = "qwen-turbo") -> QwenLLM:
    """创建通义千问LLM实例"""
    return QwenLLM(QwenConfig(api_key=api_key, model=model))


def create_ernie_llm(api_key: str, secret_key: str, model: str = "ernie-4.0-8k") -> ErnieLLM:
    """创建文心一言LLM实例"""
    return ErnieLLM(ErnieConfig(api_key=api_key, secret_key=secret_key, model=model))


def create_zhipu_llm(api_key: str, model: str = "glm-4") -> ZhipuLLM:
    """创建智谱AI LLM实例"""
    return ZhipuLLM(ZhipuConfig(api_key=api_key, model=model))
