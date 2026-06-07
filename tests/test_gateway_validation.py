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
    # Use IP literals instead of hostnames because the validator
    # now resolves the hostname and checks every A/AAAA record.
    # In sandboxed CI / corporate networks the DNS for public
    # domains may be intercepted (e.g. RFC 2544 benchmark ranges),
    # which would incorrectly fail the public-domain test.  IP
    # literals sidestep that entirely.
    req = _build_request("https://8.8.8.8/v1")
    assert req.base_url == "https://8.8.8.8/v1"
