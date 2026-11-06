# Sélection du modèle

## Présélection (catalogue et benchmarks)

| Critère | gpt-4.1 | gpt-4.1-mini |
| --- | --- | --- |
| Indice de qualité (benchmark) | 0,64 | 0,59 |
| Coût entrée / sortie (USD / M jetons, Global Standard) | 2,00 / 8,00 | 0,40 / 1,60 |
| Fenêtre de contexte | 1 047 576 jetons (300 000 en entrée), 32 768 en sortie | Identique |
| Prise en charge des outils | Appel de fonctions, Responses API, streaming | Identique |

## Évaluation

- Manuelle : 3 questions de `data/eval_dataset.jsonl` dans le playground, notées de 1 à 5.
- Automatisée : `python -m m2_models.compare_models --log-to-foundry`.

| Métrique | Mesure |
| --- | --- |
| Relevance | La réponse traite la question |
| Coherence | Lisibilité et logique |
| Groundedness | Appui sur le contexte fourni |
| Similarity | Proximité avec la réponse attendue |
| F1 | Recouvrement lexical avec la réponse attendue |

## Règle de décision

Retenir le modèle le moins cher dont la groundedness et la pertinence moyennes sont supérieures ou égales à 4.
À défaut, retenir le meilleur en groundedness et optimiser ensuite (m5_optimize).

## Décision

Modèle retenu :

Justification :
