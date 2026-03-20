"""测试 LLM 模块 (mock 测试)"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mox.core.llm import (
    BaseLLM,
    Message,
    LLMResponse,
    ModelProvider,
    OpenAILLM,
    AnthropicLLM,
    MiniMaxLLM,
    LLMFactory,
)


class TestMessage:
    def test_creation(self):
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_to_dict(self):
        msg = Message(role="assistant", content="response")
        d = msg.to_dict()
        assert d == {"role": "assistant", "content": "response"}


class TestLLMResponse:
    def test_creation(self):
        resp = LLMResponse(
            content="test response",
            model="gpt-4",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
        )
        assert resp.content == "test response"
        assert resp.model == "gpt-4"


class TestLLMFactory:
    def test_create_openai(self):
        llm = LLMFactory.create(ModelProvider.OPENAI, "gpt-4")
        assert isinstance(llm, OpenAILLM)
        assert llm.model == "gpt-4"

    def test_create_anthropic(self):
        llm = LLMFactory.create(ModelProvider.ANTHROPIC, "claude-3")
        assert isinstance(llm, AnthropicLLM)

    def test_create_minimax(self):
        llm = LLMFactory.create(ModelProvider.MINIMAX, "abab2.5-chat")
        assert isinstance(llm, MiniMaxLLM)

    def test_create_from_model_name_gpt(self):
        llm = LLMFactory.create_from_model_name("gpt-4")
        assert isinstance(llm, OpenAILLM)

    def test_create_from_model_name_claude(self):
        llm = LLMFactory.create_from_model_name("claude-3-opus")
        assert isinstance(llm, AnthropicLLM)

    def test_create_from_model_name_minimax(self):
        llm = LLMFactory.create_from_model_name("abab2.5-chat")
        assert isinstance(llm, MiniMaxLLM)

    def test_create_from_model_name_unknown(self):
        with pytest.raises(ValueError, match="Unknown model"):
            LLMFactory.create_from_model_name("unknown-model")


@pytest.mark.integration
class TestOpenAILLM:
    @pytest.mark.asyncio
    async def test_generate(self):
        with patch("mox.core.llm.AsyncOpenAI") as mock_client:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "test response"
            mock_response.model = "gpt-4"
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 20
            mock_response.usage.total_tokens = 30
            mock_response.choices[0].finish_reason = "stop"

            mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

            llm = OpenAILLM(model="gpt-4", api_key="test-key")
            messages = [Message(role="user", content="hello")]
            response = await llm.generate(messages)

            assert response.content == "test response"
            assert response.model == "gpt-4"
