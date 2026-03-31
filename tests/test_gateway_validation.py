"""测试网关 endpoint URL 安全校验。"""

import pytest
import importlib.util
from pathlib import Path
from pydantic import ValidationError


def _load_add_endpoint_request():
    module_path = Path(__file__).parent.parent / "mox" / "routes" / "gateway.py"
    spec = importlib.util.spec_from_file_location("mox.routes.gateway", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.AddEndpointRequest


AddEndpointRequest = _load_add_endpoint_request()


def _build_request(base_url: str) -> AddEndpointRequest:
    return AddEndpointRequest(
        name="test-endpoint",
        provider="openai",
        model="gpt-4",
        base_url=base_url,
    )


def test_rejects_localhost_address():
    with pytest.raises(ValidationError):
        _build_request("http://localhost:8000")


def test_rejects_private_ip_address():
    with pytest.raises(ValidationError):
        _build_request("http://10.0.0.5:8080")


def test_rejects_resolved_localhost_name():
    with pytest.raises(ValidationError):
        _build_request("https://localhost")


def test_allows_public_domain():
    req = _build_request("https://api.openai.com/v1")
    assert req.base_url == "https://api.openai.com/v1"
