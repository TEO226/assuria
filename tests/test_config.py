"""Tests de la configuration."""
import pytest

from common import config


@pytest.mark.parametrize("value", [
    "https://res.openai.azure.com/",
    "https://res.openai.azure.com",
    "https://res.openai.azure.com/openai/v1",
    "https://res.openai.azure.com/openai/v1/",
])
def test_eval_endpoint_normalise(monkeypatch, value):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", value)
    assert config.eval_model_config()["azure_endpoint"] == "https://res.openai.azure.com/"


def test_estimate_cost():
    assert config.estimate_cost("gpt-4.1-mini", 2000, 150) == pytest.approx(0.00104)
    assert config.estimate_cost("modele-inconnu", 2000, 150) == 0.0
