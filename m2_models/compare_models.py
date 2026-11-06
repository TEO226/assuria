"""Compare deux déploiements sur le jeu data/eval_dataset.jsonl.

Mesures : pertinence, cohérence, ancrage, similarité (modèle juge), F1, latence, coût estimé.
Sorties : outputs/comparaison_modeles*.csv et .md

python -m m2_models.compare_models [--models A B] [--log-to-foundry]
"""
from __future__ import annotations

import argparse
import json
import statistics
import time

from common.config import (CANDIDATE_MODEL, CHAT_MODEL, DATA, OUTPUTS, PROJECT_ENDPOINT,
                           estimate_cost, eval_model_config, get_openai_client)

INSTRUCTIONS = ("Tu es l'assistant de Kéné Assurances IARD. Réponds en français, en 2 phrases maximum, "
                "uniquement à partir du contexte fourni. Si le contexte ne permet pas de répondre, dis-le.")
METRICS = ("relevance", "coherence", "groundedness", "similarity", "f1_score")


def load_dataset() -> list[dict]:
    with (DATA / "eval_dataset.jsonl").open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def generate(model: str, rows: list[dict]) -> list[dict]:
    client = get_openai_client()
    results = []
    for row in rows:
        start = time.perf_counter()
        resp = client.responses.create(
            model=model, instructions=INSTRUCTIONS, temperature=0,
            input=f"Contexte :\n{row['context']}\n\nQuestion : {row['query']}",
        )
        results.append(row | {
            "model": model, "response": resp.output_text.strip(),
            "latency_s": round(time.perf_counter() - start, 2),
            "input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens,
        })
        print(f"  [{model}] {row['query'][:60]} ({results[-1]['latency_s']} s)")
    return results


def score(results: list[dict]) -> list[dict]:
    from azure.ai.evaluation import (CoherenceEvaluator, F1ScoreEvaluator, GroundednessEvaluator,
                                     RelevanceEvaluator, SimilarityEvaluator)
    cfg = eval_model_config()
    relevance, coherence = RelevanceEvaluator(cfg), CoherenceEvaluator(cfg)
    groundedness, similarity, f1 = GroundednessEvaluator(cfg), SimilarityEvaluator(cfg), F1ScoreEvaluator()
    for r in results:
        r["relevance"] = relevance(query=r["query"], response=r["response"])["relevance"]
        r["coherence"] = coherence(query=r["query"], response=r["response"])["coherence"]
        r["groundedness"] = groundedness(query=r["query"], response=r["response"],
                                         context=r["context"])["groundedness"]
        r["similarity"] = similarity(query=r["query"], response=r["response"],
                                     ground_truth=r["ground_truth"])["similarity"]
        r["f1_score"] = f1(response=r["response"], ground_truth=r["ground_truth"])["f1_score"]
    return results


def summarize(results: list[dict], models: list[str]) -> list[dict]:
    summary = []
    for m in models:
        rows = [r for r in results if r["model"] == m]
        cost = estimate_cost(m, sum(r["input_tokens"] for r in rows), sum(r["output_tokens"] for r in rows))
        summary.append({
            "modele": m,
            **{k: round(statistics.mean(float(r[k]) for r in rows), 2) for k in METRICS},
            "latence_moy_s": round(statistics.mean(r["latency_s"] for r in rows), 2),
            "cout_usd_1000_questions": round(cost * 1000 / len(rows), 2),
        })
    return summary


def write_reports(results: list[dict], summary: list[dict]) -> None:
    import pandas as pd
    pd.DataFrame(results).to_csv(OUTPUTS / "comparaison_modeles_detail.csv", index=False)
    df = pd.DataFrame(summary)
    df.to_csv(OUTPUTS / "comparaison_modeles.csv", index=False)
    lines = ["# Comparaison des modèles", "", "Notes de 1 à 5, F1 de 0 à 1.", "",
             "| " + " | ".join(df.columns) + " |", "|" + " --- |" * len(df.columns)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    (OUTPUTS / "comparaison_modeles.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines))


def log_to_foundry(results: list[dict]) -> None:
    from azure.ai.evaluation import GroundednessEvaluator, RelevanceEvaluator, evaluate
    path = OUTPUTS / "eval_input.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps({k: r[k] for k in ("model", "query", "response", "context", "ground_truth")},
                               ensure_ascii=False) + "\n")
    cfg = eval_model_config()
    evaluate(data=str(path), evaluation_name="assuria-comparaison-modeles",
             evaluators={"relevance": RelevanceEvaluator(cfg), "groundedness": GroundednessEvaluator(cfg)},
             azure_ai_project=PROJECT_ENDPOINT)
    print("Évaluation publiée dans le portail Foundry.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=[CHAT_MODEL, CANDIDATE_MODEL])
    parser.add_argument("--log-to-foundry", action="store_true")
    args = parser.parse_args()

    rows = load_dataset()
    results = []
    for model in args.models:
        print(f"Génération : {model}")
        results += generate(model, rows)
    print("Notation")
    results = score(results)
    write_reports(results, summarize(results, args.models))
    if args.log_to_foundry:
        log_to_foundry(results)


if __name__ == "__main__":
    main()
