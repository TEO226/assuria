"""Fonctions métier appelées par le modèle (outil function).

Barème : data/docs/02_tarif_auto.md (fictif).
"""
from __future__ import annotations

import json
import math

from common.config import DATA

RC_BASE = [(4, 65_000), (7, 85_000), (10, 110_000), (14, 140_000), (math.inf, 180_000)]
USAGE = {"prive": 1.00, "professionnel": 1.20, "transport_public": 1.60}
ZONE = {"grande_agglomeration": 1.10, "autre": 1.00}
FORMULES = {
    "tiers_simple": ["defense_recours"],
    "tiers_etendu": ["defense_recours", "incendie", "vol", "bris_de_glace"],
    "tous_risques": ["defense_recours", "incendie", "vol", "bris_de_glace",
                     "dommages_tous_accidents", "individuelle_conducteur"],
}
ACCESSOIRES = 5_000
TAUX_TAXE = 0.10


def _garantie(nom: str, valeur: int) -> int:
    return {
        "defense_recours": 7_500,
        "incendie": round(valeur * 0.0025),
        "vol": round(valeur * 0.0035),
        "bris_de_glace": 15_000,
        "dommages_tous_accidents": round(valeur * 0.035),
        "individuelle_conducteur": 12_000,
    }[nom]


def calculer_prime_auto(puissance_cv: int, usage: str, zone: str, formule: str,
                        valeur_vehicule_fcfa: int = 0, age_vehicule_ans: int = 0,
                        coefficient_bonus_malus: float = 1.0) -> dict:
    if puissance_cv < 2:
        return {"erreur": "La puissance fiscale doit être d'au moins 2 CV."}
    if usage not in USAGE or zone not in ZONE or formule not in FORMULES:
        return {"erreur": "Usage, zone ou formule inconnu.",
                "usages": list(USAGE), "zones": list(ZONE), "formules": list(FORMULES)}
    if not 0.5 <= coefficient_bonus_malus <= 3.5:
        return {"erreur": "Le coefficient bonus-malus doit être compris entre 0,50 et 3,50."}
    if formule == "tous_risques" and age_vehicule_ans >= 8:
        return {"erreur": "La formule Tous risques n'est proposée qu'aux véhicules de moins de 8 ans."}
    if formule != "tiers_simple" and valeur_vehicule_fcfa <= 0:
        return {"erreur": "La valeur vénale du véhicule est nécessaire pour cette formule."}

    rc_base = next(p for seuil, p in RC_BASE if puissance_cv <= seuil)
    rc = rc_base * USAGE[usage] * ZONE[zone] * coefficient_bonus_malus
    garanties = {g: _garantie(g, valeur_vehicule_fcfa) for g in FORMULES[formule]}
    prime_nette = rc + sum(garanties.values())
    taxes = prime_nette * TAUX_TAXE
    total = math.ceil((prime_nette + ACCESSOIRES + taxes) / 100) * 100

    return {
        "formule": formule,
        "prime_rc_base_fcfa": rc_base,
        "prime_rc_apres_coefficients_fcfa": round(rc),
        "garanties_fcfa": garanties,
        "prime_nette_fcfa": round(prime_nette),
        "accessoires_fcfa": ACCESSOIRES,
        "taxes_fcfa": round(taxes),
        "prime_totale_annuelle_fcfa": total,
        "avertissement": "Tarif indicatif issu d'un barème fictif, hors offre contractuelle.",
    }


def consulter_sinistre(numero_dossier: str) -> dict:
    dossiers = json.loads((DATA / "sinistres_suivi.json").read_text(encoding="utf-8"))
    dossier = dossiers.get(numero_dossier.strip().upper())
    if not dossier:
        return {"erreur": f"Aucun dossier {numero_dossier}. Format attendu : SIN-AAAA-NNNN."}
    # L'identité de l'assuré n'est jamais transmise au modèle.
    return {k: v for k, v in dossier.items() if k != "assure"} | {"numero": numero_dossier.upper()}


FUNCTION_TOOLS = [
    {
        "type": "function",
        "name": "calculer_prime_auto",
        "description": "Calcule la prime annuelle indicative d'un contrat Kéné Auto. "
                       "Demander à l'utilisateur les informations manquantes avant d'appeler.",
        "parameters": {
            "type": "object",
            "properties": {
                "puissance_cv": {"type": "integer", "description": "Puissance fiscale en chevaux (CV)"},
                "usage": {"type": "string", "enum": list(USAGE)},
                "zone": {"type": "string", "enum": list(ZONE),
                         "description": "grande_agglomeration = Ouagadougou ou Bobo-Dioulasso"},
                "formule": {"type": "string", "enum": list(FORMULES)},
                "valeur_vehicule_fcfa": {"type": "integer", "description": "Valeur vénale, 0 si tiers simple"},
                "age_vehicule_ans": {"type": "integer"},
                "coefficient_bonus_malus": {"type": "number", "description": "1.0 par défaut"},
            },
            "required": ["puissance_cv", "usage", "zone", "formule"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "consulter_sinistre",
        "description": "Donne le statut et la prochaine étape d'un dossier sinistre à partir de son numéro.",
        "parameters": {
            "type": "object",
            "properties": {"numero_dossier": {"type": "string", "description": "Format SIN-AAAA-NNNN"}},
            "required": ["numero_dossier"],
            "additionalProperties": False,
        },
    },
]

REGISTRY = {"calculer_prime_auto": calculer_prime_auto, "consulter_sinistre": consulter_sinistre}


def run_function(name: str, arguments_json: str) -> str:
    func = REGISTRY.get(name)
    if func is None:
        return json.dumps({"erreur": f"Fonction inconnue : {name}"}, ensure_ascii=False)
    try:
        args = json.loads(arguments_json or "{}")
        return json.dumps(func(**args), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        return json.dumps({"erreur": f"Arguments invalides : {exc}"}, ensure_ascii=False)
