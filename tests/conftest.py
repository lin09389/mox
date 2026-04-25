"""测试 fixtures"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mox.core.llm import Message


@pytest.fixture
def mock_llm_response():
    def _create_response(content: str = "test response"):
        response = MagicMock()
        response.content = content
        response.model = "gpt-4"
        response.usage.input_tokens = 10
        response.usage.output_tokens = 20
        response.usage.total_tokens = 30
        response.stop_reason = "stop"
        return response

    return _create_response


@pytest.fixture
def sample_messages():
    return [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello, how are you?"),
    ]


@pytest.fixture
def mock_openai_client():
    with patch("mox.core.llm.AsyncOpenAI") as mock:
        yield mock


@pytest.fixture
def mock_anthropic_client():
    with patch("mox.core.llm.AsyncAnthropic") as mock:
        yield mock
