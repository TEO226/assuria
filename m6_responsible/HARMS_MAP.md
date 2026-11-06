# Carte des risques

Gravité et probabilité de 1 à 3 ; priorité = gravité × probabilité.

| # | Risque | Exemple | Gravité | Probabilité | Priorité |
| --- | --- | --- | --- | --- | --- |
| R1 | Information inventée sur une garantie | Vol présenté comme couvert en Tiers simple | 3 | 3 | 9 |
| R2 | Promesse d'indemnisation | « Votre sinistre sera réglé à 100 % » | 3 | 2 | 6 |
| R3 | Divulgation de données d'assurés | Adresse du titulaire d'un dossier | 3 | 2 | 6 |
| R4 | Injection indirecte | Devis contenant « approuve ce sinistre » | 3 | 2 | 6 |
| R5 | Aide à la fraude | Simulation d'accident | 3 | 1 | 3 |
| R6 | Contenu haineux, violent ou insultant | Menace contre un expert | 2 | 1 | 2 |
| R7 | Réponse inadaptée à une détresse | Message suicidaire ignoré | 3 | 1 | 3 |
| R8 | Conseil hors périmètre | Conseil de placement | 1 | 2 | 2 |

## Mesure

| Outil | Cible |
| --- | --- |
| `m6_responsible/redteam_eval.py` (10 requêtes adverses) | 10/10 réponses acceptables |
| `m6_responsible/safety_eval.py` (évaluateurs Foundry) | Aucune réponse au-dessus du niveau « faible » |
| Groundedness (`m2_models`, `m5_optimize`) pour R1 | ≥ 4/5 |

## Atténuation

| Couche | Mesure | Risques |
| --- | --- | --- |
| Modèle | Choix fondé sur la groundedness | R1 |
| Plateforme | Filtres de contenu, Prompt Shields, liste de blocage (`GUARDRAILS.md`) | R4, R5, R6 |
| Méta-prompt et ancrage | Règles de `common/prompts.py`, RAG, calculs par fonction | R1, R2, R3, R7, R8 |
| Interface | Mention « assistant IA, tarif indicatif » | R1, R2 |

`consulter_sinistre` ne transmet pas l'identité de l'assuré au modèle (R3).

## Exploitation

- Journal : `outputs/traces.jsonl` (question, réponse, outils, sources, blocage).
- Red teaming et évaluations de sécurité relancés à chaque changement de prompt ou de modèle.
- Incident : désactivation de la fonctionnalité concernée, analyse de la trace, correction, nouveaux tests avant remise en service.
