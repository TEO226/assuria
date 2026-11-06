"""Tests du barème et des fonctions métier (sans appel Azure)."""
import json

from common.tools import calculer_prime_auto, consulter_sinistre, run_function


def test_tiers_simple_6cv_prive_autre_zone():
    r = calculer_prime_auto(6, "prive", "autre", "tiers_simple")
    # RC 85 000 + défense-recours 7 500 = 92 500 ; + 5 000 accessoires + 9 250 taxes = 106 750 -> 106 800
    assert r["prime_nette_fcfa"] == 92_500
    assert r["prime_totale_annuelle_fcfa"] == 106_800


def test_tiers_etendu_avec_coefficients():
    r = calculer_prime_auto(6, "prive", "grande_agglomeration", "tiers_etendu",
                            valeur_vehicule_fcfa=6_000_000, age_vehicule_ans=4, coefficient_bonus_malus=0.8)
    # RC 85 000 × 1,10 × 0,80 = 74 800 ; garanties 7 500 + 15 000 + 21 000 + 15 000 = 58 500
    assert r["prime_rc_apres_coefficients_fcfa"] == 74_800
    assert r["prime_nette_fcfa"] == 133_300
    assert r["prime_totale_annuelle_fcfa"] == 151_700


def test_tous_risques_refuse_vehicule_ancien():
    assert "erreur" in calculer_prime_auto(8, "prive", "autre", "tous_risques", 5_000_000, 9)


def test_valeur_obligatoire_hors_tiers_simple():
    assert "erreur" in calculer_prime_auto(8, "prive", "autre", "tiers_etendu")


def test_sinistre_sans_donnees_personnelles():
    r = consulter_sinistre("sin-2026-0101")
    assert r["statut"] == "En expertise" and "assure" not in r


def test_run_function_arguments_invalides():
    assert "erreur" in json.loads(run_function("calculer_prime_auto", '{"puissance_cv": 6}'))
