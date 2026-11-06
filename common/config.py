"""Configuration et clients Microsoft Foundry."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(exist_ok=True)

load_dotenv(ROOT / ".env")


def env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(f"Variable {name} manquante dans .env (voir .env.example).")
    return value or ""


PROJECT_ENDPOINT = env("FOUNDRY_PROJECT_ENDPOINT")
CHAT_MODEL = env("CHAT_MODEL_DEPLOYMENT", "gpt-4.1-mini")
CANDIDATE_MODEL = env("CANDIDATE_MODEL_DEPLOYMENT", "gpt-4.1")
EVAL_MODEL = env("EVAL_MODEL_DEPLOYMENT", "gpt-4.1")
WEB_SEARCH_TOOL_TYPE = env("WEB_SEARCH_TOOL_TYPE", "web_search")

# USD par million de jetons (entrée, sortie), déploiement Global Standard.
MODEL_PRICES = {
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = MODEL_PRICES.get(model, (0.0, 0.0))
    return (input_tokens * price_in + output_tokens * price_out) / 1e6


@lru_cache(maxsize=1)
def get_credential():
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()


@lru_cache(maxsize=1)
def get_project_client():
    from azure.ai.projects import AIProjectClient

    return AIProjectClient(endpoint=env("FOUNDRY_PROJECT_ENDPOINT", required=True),
                           credential=get_credential())


@lru_cache(maxsize=1)
def get_openai_client():
    return get_project_client().get_openai_client()


def eval_model_config() -> dict:
    """Modèle juge pour azure-ai-evaluation (point de terminaison Azure OpenAI de la ressource)."""
    # Le SDK d'évaluation ajoute lui-même le chemin : on retire un éventuel /openai/v1.
    endpoint = env("AZURE_OPENAI_ENDPOINT", required=True).split("/openai")[0].rstrip("/") + "/"
    return {
        "azure_endpoint": endpoint,
        "azure_deployment": EVAL_MODEL,
        "api_version": env("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    }


def save_env_value(name: str, value: str) -> None:
    path = ROOT / ".env"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    lines = [line for line in lines if not line.startswith(f"{name}=")]
    lines.append(f"{name}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ[name] = value
