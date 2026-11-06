"""Moteur de conversation : Responses API, outils, journal des échanges."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import openai

from common.config import CHAT_MODEL, OUTPUTS, WEB_SEARCH_TOOL_TYPE, env, get_openai_client
from common.prompts import SYSTEM_PROMPT
from common.tools import FUNCTION_TOOLS, run_function

TRACE_FILE = OUTPUTS / "traces.jsonl"
MAX_TOOL_ROUNDS = 5

SAFE_REFUSAL = ("Je ne peux pas répondre à cette demande. Je peux en revanche vous renseigner sur nos "
                "produits, vos garanties ou le suivi d'un sinistre.")


def build_tools(file_search: bool = True, functions: bool = True,
                code_interpreter: bool = False, web_search: bool = False,
                code_file_ids: list[str] | None = None) -> list[dict]:
    tools: list[dict] = []
    vector_store_id = env("VECTOR_STORE_ID")
    if file_search and vector_store_id:
        tools.append({"type": "file_search", "vector_store_ids": [vector_store_id], "max_num_results": 5})
    if functions:
        tools.extend(FUNCTION_TOOLS)
    if code_interpreter:
        tools.append({"type": "code_interpreter",
                      "container": {"type": "auto", "file_ids": code_file_ids or []}})
    if web_search:
        tools.append({"type": WEB_SEARCH_TOOL_TYPE})
    return tools


@dataclass
class Turn:
    text: str
    citations: list[str] = field(default_factory=list)
    tool_calls: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    blocked: bool = False
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0


class AssurIA:
    def __init__(self, model: str = CHAT_MODEL, instructions: str = SYSTEM_PROMPT,
                 tools: list[dict] | None = None, temperature: float | None = 0.2,
                 max_output_tokens: int = 800):
        self.client = get_openai_client()
        self.model = model
        self.instructions = instructions
        self.tools = build_tools() if tools is None else tools
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.previous_response_id: str | None = None

    def reset(self) -> None:
        self.previous_response_id = None

    def _create(self, input_items, previous_id):
        kwargs = dict(model=self.model, instructions=self.instructions, input=input_items,
                      max_output_tokens=self.max_output_tokens)
        # Foundry rejette previous_response_id=null.
        if previous_id:
            kwargs["previous_response_id"] = previous_id
        if self.tools:
            kwargs["tools"] = self.tools
        if self.temperature is not None:  # non supportée par les modèles de raisonnement
            kwargs["temperature"] = self.temperature
        return self.client.responses.create(**kwargs)

    def ask(self, message: str) -> Turn:
        start = time.perf_counter()
        turn = Turn(text="")
        try:
            response = self._create(message, self.previous_response_id)
            for _ in range(MAX_TOOL_ROUNDS):
                calls = [o for o in response.output if o.type == "function_call"]
                if not calls:
                    break
                outputs = []
                for call in calls:
                    turn.tool_calls.append(f"{call.name}({call.arguments})")
                    outputs.append({"type": "function_call_output", "call_id": call.call_id,
                                    "output": run_function(call.name, call.arguments)})
                self._accumulate_usage(turn, response)
                response = self._create(outputs, response.id)
        except openai.BadRequestError as exc:
            if "content_filter" in str(exc) or "content management policy" in str(exc):
                turn.text, turn.blocked = SAFE_REFUSAL, True
                turn.latency_s = round(time.perf_counter() - start, 2)
                self._trace(message, turn)
                return turn
            raise

        self.previous_response_id = response.id
        self._accumulate_usage(turn, response)
        turn.text = response.output_text or SAFE_REFUSAL
        self._collect_annotations(response, turn)
        turn.latency_s = round(time.perf_counter() - start, 2)
        self._trace(message, turn)
        return turn

    @staticmethod
    def _accumulate_usage(turn: Turn, response) -> None:
        if getattr(response, "usage", None):
            turn.input_tokens += response.usage.input_tokens or 0
            turn.output_tokens += response.usage.output_tokens or 0

    def _collect_annotations(self, response, turn: Turn) -> None:
        for item in response.output:
            if item.type in ("code_interpreter_call", "file_search_call", "web_search_call"):
                turn.tool_calls.append(item.type)
            if item.type != "message":
                continue
            for part in item.content:
                for ann in getattr(part, "annotations", None) or []:
                    if ann.type == "file_citation" and ann.filename not in turn.citations:
                        turn.citations.append(ann.filename)
                    elif ann.type == "url_citation" and ann.url not in turn.citations:
                        turn.citations.append(ann.url)
                    elif ann.type == "container_file_citation":
                        turn.files.append(self._download(ann))

    def _download(self, ann) -> str:
        target = OUTPUTS / ann.filename
        content = self.client.containers.files.content.retrieve(
            file_id=ann.file_id, container_id=ann.container_id)
        target.write_bytes(content.read())
        return str(target)

    def _trace(self, message: str, turn: Turn) -> None:
        record = {
            "horodatage": datetime.now(timezone.utc).isoformat(), "modele": self.model,
            "question": message, "reponse": turn.text, "bloque": turn.blocked,
            "outils": turn.tool_calls, "sources": turn.citations,
            "jetons_entree": turn.input_tokens, "jetons_sortie": turn.output_tokens,
            "latence_s": turn.latency_s,
        }
        with TRACE_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
