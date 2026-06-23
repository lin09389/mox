"""Tests for Prometheus business metrics."""

from prometheus_client import generate_latest

from mox.core.prometheus_metrics import record_attack, record_defense


def test_record_attack_exposes_metrics():
    record_attack("prompt_injection", "gpt-4", "success", 0.42)
    output = generate_latest().decode()
    assert "mox_attack_requests_total" in output
    assert "mox_attack_duration_seconds" in output
    assert 'attack_type="prompt_injection"' in output


def test_record_defense_exposes_metrics():
    record_defense("input_filter", "input", True, 0.05)
    output = generate_latest().decode()
    assert "mox_defense_requests_total" in output
    assert "mox_defense_duration_seconds" in output
    assert 'defense_type="input_filter"' in output