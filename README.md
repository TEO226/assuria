# AssurIA

Assistant conversationnel pour un assureur IARD, construit sur Microsoft Foundry avec la Responses API.

Réalisé dans le cadre du parcours Microsoft Learn *Develop generative AI apps in Azure* (cours AI-103T00).
La compagnie (Kéné Assurances IARD), ses produits, son barème et ses sinistres sont fictifs.

## Fonctionnalités

- Réponses sur les produits à partir des documents de la compagnie (`file_search`, RAG).
- Calcul de prime auto et suivi de dossier sinistre par appel de fonction (`function`).
- Analyse du portefeuille de sinistres avec graphiques (`code_interpreter`).
- Recherche web optionnelle (`web_search`).
- Garde-fous de contenu, red teaming et évaluations de sécurité.
- Journal des échanges (question, outils, sources, jetons, latence).

## Architecture

```
Streamlit / CLI
      │
common/assistant.py ── Responses API ──► Projet Microsoft Foundry
      │                                   ├── garde-fou (filtres, Prompt Shields)
      │                                   ├── modèle déployé
      │                                   └── outils : file_search, code_interpreter, web_search
      └── common/tools.py ◄── function_call (prime, sinistre)
```

Authentification sans clé (`DefaultAzureCredential`, rôle Azure AI User sur le projet).

## Stack

Python 3.10+, `azure-ai-projects` 2.x, `openai`, `azure-ai-evaluation`, Streamlit, pandas, pytest.

## Structure

```
common/           clients Foundry, moteur de conversation, fonctions métier, prompts
data/             documents produits, sinistres 2025, jeux d'évaluation, red teaming, fine-tuning
m1_preparation/   vérification de l'environnement, script de déploiement, note d'architecture
m2_models/        comparaison et évaluation de modèles
m3_chat/          chat Responses API et ChatCompletions
m4_tools/         vector store, démonstration des outils, chat outillé
m5_optimize/      expérimentation prompt / RAG, fine-tuning
m6_responsible/   carte des risques, garde-fous, red teaming, évaluations de sécurité
app/              interface Streamlit et CLI
tests/            tests hors ligne
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # renseigner le projet Foundry et les déploiements
az login
```

Prérequis Azure : un projet Microsoft Foundry, deux déploiements de chat (par exemple `gpt-4.1-mini` et `gpt-4.1`)
et le rôle Azure AI User sur le projet.

## Utilisation

```bash
python -m m1_preparation.check_setup            # vérifier la configuration
python -m m4_tools.setup_vector_store           # indexer les documents
python -m streamlit run app/streamlit_app.py    # lancer l'application
```

Autres scripts :

| Commande | Rôle |
| --- | --- |
| `python -m m2_models.compare_models [--log-to-foundry]` | Comparer deux modèles : qualité, latence, coût |
| `python -m m3_chat.chat_responses [--stream]` | Chat multi-tours, Responses API |
| `python -m m3_chat.chat_completions` | Chat multi-tours, ChatCompletions |
| `python -m m4_tools.demo_tools [--web]` | Un scénario par outil |
| `python -m m5_optimize.experiment_prompting` | Comparer prompt minimal, structuré, few-shot, avec ou sans RAG |
| `python -m m5_optimize.build_finetune_dataset` | Générer le jeu de fine-tuning |
| `python -m m5_optimize.finetune_job` | Lancer un fine-tuning (payant) |
| `python -m m6_responsible.redteam_eval` | Red teaming |
| `python -m m6_responsible.safety_eval` | Évaluations de sécurité |

Les rapports sont écrits dans `outputs/`.

## Tests

```bash
python -m pytest -q
```

Barème, confidentialité des données, boucle d'appel de fonctions et configuration, sans appel à Azure.

## Coûts

Les appels aux modèles, les outils et l'évaluation sont facturés à l'usage. Le fine-tuning et l'hébergement d'un
modèle fine-tuné sont nettement plus coûteux : supprimer le déploiement après les essais.
