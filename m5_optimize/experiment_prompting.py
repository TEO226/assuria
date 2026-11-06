"""Compare plusieurs configurations (prompt, RAG, température, modèle) sur eval_dataset.jsonl.

Le contexte n'est pas fourni dans la question : seule la configuration fait la différence.
Sorties : outputs/optimisation_resume.csv et optimisation_detail.csv

python -m m5_optimize.experiment_prompting
"""
from __future__ import annotations

import json
import statistics

from common.assistant import AssurIA, build_tools
from common.config import CHAT_MODEL, DATA, OUTPUTS, env, eval_model_config
from common.prompts import V0_BASELINE, V1_STRUCTURED, V2_FEW_SHOT

CONFIGS = {
    "A_minimal_sans_rag": dict(instructions=V0_BASELINE, rag=False, temperature=0.9, model=CHAT_MODEL),
    "B_structure_sans_rag": dict(instructions=V1_STRUCTURED, rag=False, temperature=0.2, model=CHAT_MODEL),
    "C_structure_rag": dict(instructions=V1_STRUCTURED, rag=True, temperature=0.2, model=CHAT_MODEL),
    "D_fewshot_rag": dict(instructions=V2_FEW_SHOT, rag=True, temperature=0.2, model=CHAT_MODEL),
}
if env("FINETUNED_MODEL_DEPLOYMENT"):
    CONFIGS["E_finetune_rag"] = dict(instructions=V1_STRUCTURED, rag=True, temperature=0.2,
                                     model=env("FINETUNED_MODEL_DEPLOYMENT"))

MAX_WORDS = 120


def main() -> None:
    from azure.ai.evaluation import RelevanceEvaluator, SimilarityEvaluator

    if not env("VECTOR_STORE_ID"):
        raise SystemExit("VECTOR_STORE_ID vide : lancer python -m m4_tools.setup_vector_store")
    rows = [json.loads(line) for line in (DATA / "eval_dataset.jsonl").open(encoding="utf-8") if line.strip()]
    cfg = eval_model_config()
    relevance, similarity = RelevanceEvaluator(cfg), SimilarityEvaluator(cfg)

    summary, details = [], []
    for name, c in CONFIGS.items():
        print(f"\n== {name} ==")
        scores = {"relevance": [], "similarity": [], "format_ok": [], "tokens": []}
        for row in rows:
            bot = AssurIA(model=c["model"], instructions=c["instructions"], temperature=c["temperature"],
                          tools=build_tools(file_search=c["rag"], functions=False))
            turn = bot.ask(row["query"])
            rel = relevance(query=row["query"], response=turn.text)["relevance"]
            sim = similarity(query=row["query"], response=turn.text, ground_truth=row["ground_truth"])["similarity"]
            scores["relevance"].append(float(rel))
            scores["similarity"].append(float(sim))
            scores["format_ok"].append(len(turn.text.split()) <= MAX_WORDS)
            scores["tokens"].append(turn.input_tokens + turn.output_tokens)
            details.append({"config": name, "query": row["query"], "response": turn.text,
                            "relevance": rel, "similarity": sim, "sources": turn.citations})
            print(f"  pertinence {rel} | similarité {sim} | {row['query'][:50]}")
        summary.append({
            "configuration": name,
            "pertinence_moy": round(statistics.mean(scores["relevance"]), 2),
            "similarite_moy": round(statistics.mean(scores["similarity"]), 2),
            "format_respecte_%": round(100 * sum(scores["format_ok"]) / len(rows)),
            "jetons_moy": round(statistics.mean(scores["tokens"])),
        })

    import pandas as pd
    pd.DataFrame(details).to_csv(OUTPUTS / "optimisation_detail.csv", index=False)
    df = pd.DataFrame(summary)
    df.to_csv(OUTPUTS / "optimisation_resume.csv", index=False)
    print("\n" + df.to_string(index=False))


if __name__ == "__main__":
    main()
