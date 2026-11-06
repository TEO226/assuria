# Architecture

## Capacités et services

| Besoin | Capacité | Service |
| --- | --- | --- |
| Dialogue en langage naturel | LLM | Modèle déployé dans Microsoft Foundry |
| Réponses fondées sur les documents | Recherche sémantique, RAG | `file_search` + vector store |
| Calcul de prime, lecture de dossier | Appel de fonction | `function`, exécutée en Python |
| Analyse du fichier des sinistres | Exécution de code | `code_interpreter` |
| Actualité réglementaire | Recherche web | `web_search` |
| Filtrage des contenus | Modération | Garde-fous Foundry (Azure AI Content Safety) |
| Mesure qualité et sécurité | Évaluation | `azure-ai-evaluation`, portail Foundry |

## Choix techniques

- SDK : `azure-ai-projects` pour le projet (déploiements, connexions), client OpenAI obtenu par
  `get_openai_client()` pour les réponses, fichiers, vector stores et fine-tuning.
- Authentification : `DefaultAzureCredential` (Azure CLI en local, identité managée en production). Aucune clé d'API.
- Langage : Python 3.10+.

## Ressources Azure

- Groupe de ressources `rg-assuria`.
- Ressource Microsoft Foundry et projet `assuria`.
- Déploiements : un modèle de chat, un modèle candidat, un modèle juge pour l'évaluation.
- Rôle Azure AI User pour le développeur.

## Risques identifiés à la conception

Hallucination sur une garantie, promesse d'indemnisation, fuite de données d'assurés, détournement du prompt.
Détail dans `m6_responsible/HARMS_MAP.md`.
