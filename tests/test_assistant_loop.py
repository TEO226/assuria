"""Tests de la boucle d'appel de fonctions avec un client simulé."""
from types import SimpleNamespace as NS

import common.assistant as assistant


class FakeResponses:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        usage = NS(input_tokens=10, output_tokens=5)
        if len(self.calls) == 1:
            call = NS(type="function_call", name="calculer_prime_auto", call_id="c1",
                      arguments='{"puissance_cv": 6, "usage": "prive", "zone": "autre", "formule": "tiers_simple"}')
            return NS(id="r1", output=[call], output_text="", usage=usage)
        cite = NS(type="file_citation", filename="02_tarif_auto.md")
        msg = NS(type="message", content=[NS(annotations=[cite])])
        return NS(id="r2", output=[msg], output_text="La prime est de 106 800 FCFA.", usage=usage)


def test_function_loop(monkeypatch, tmp_path):
    fake = NS(responses=FakeResponses())
    monkeypatch.setattr(assistant, "get_openai_client", lambda: fake)
    monkeypatch.setattr(assistant, "TRACE_FILE", tmp_path / "traces.jsonl")
    bot = assistant.AssurIA(tools=[{"type": "function", "name": "calculer_prime_auto"}])
    turn = bot.ask("Prime pour une 6 CV en tiers simple ?")

    second = fake.responses.calls[1]
    assert second["previous_response_id"] == "r1"
    assert second["input"][0]["type"] == "function_call_output"
    assert '"prime_totale_annuelle_fcfa": 106800' in second["input"][0]["output"]
    assert "instructions" in second
    assert turn.text == "La prime est de 106 800 FCFA."
    assert turn.citations == ["02_tarif_auto.md"]
    assert turn.input_tokens == 20 and bot.previous_response_id == "r2"
    assert (tmp_path / "traces.jsonl").exists()


def test_premier_tour_sans_previous_response_id(monkeypatch, tmp_path):
    fake = NS(responses=FakeResponses())
    monkeypatch.setattr(assistant, "get_openai_client", lambda: fake)
    monkeypatch.setattr(assistant, "TRACE_FILE", tmp_path / "traces.jsonl")
    assistant.AssurIA(tools=[]).ask("Bonjour")
    assert "previous_response_id" not in fake.responses.calls[0]
