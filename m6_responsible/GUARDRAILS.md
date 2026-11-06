# Garde-fou `assuria-guardrail`

Configuration dans le portail Foundry, menu Garde-fous du projet.

| Contrôle | Entrée | Sortie |
| --- | --- | --- |
| Haine et iniquité | Bloquer dès Moyen | Bloquer dès Faible |
| Violence | Bloquer dès Moyen | Bloquer dès Faible |
| Sexuel | Bloquer dès Faible | Bloquer dès Faible |
| Auto-agression | Annoter uniquement | Bloquer dès Faible |
| Prompt Shields, attaques directes | Activé, bloquer | — |
| Prompt Shields, attaques indirectes | Activé, bloquer | — |
| Matériel protégé (texte) | — | Activé |

L'auto-agression est seulement annotée en entrée pour que le message d'une personne en détresse reçoive
la réponse d'orientation définie dans le méta-prompt.

## Liste de blocage

`assuria-blocklist`, appliquée en entrée et en sortie : « faux constat », « faux sinistre », « double indemnisation ».

## Application

Associer le garde-fou aux déploiements `CHAT_MODEL_DEPLOYMENT` et, le cas échéant, `FINETUNED_MODEL_DEPLOYMENT`.

## Vérification

- La requête rt04 de `data/redteam_prompts.jsonl` est bloquée dans le playground.
- `python -m m6_responsible.redteam_eval` signale les requêtes bloquées (`bloque = True`) ;
  l'application renvoie alors un refus neutre.
