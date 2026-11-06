"""Génère data/sinistres_2025.csv (400 sinistres fictifs, tirage déterministe).

python data/generate_sinistres_csv.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(2025)

# branche -> (poids dans le portefeuille, {nature: (montant min, montant max) en FCFA})
BRANCHES = {
    "Automobile": (0.62, {"Collision": (150_000, 3_500_000), "Bris de glace": (60_000, 350_000),
                          "Vol": (1_500_000, 9_000_000), "Incendie": (800_000, 7_000_000)}),
    "Habitation": (0.20, {"Dégât des eaux": (80_000, 1_200_000), "Incendie": (500_000, 8_000_000),
                          "Vol par effraction": (150_000, 2_500_000), "Dommages électriques": (60_000, 900_000)}),
    "Professionnelle": (0.12, {"Incendie": (2_000_000, 40_000_000), "Vol": (400_000, 6_000_000),
                               "Dégât des eaux": (300_000, 5_000_000), "Bris de machine": (500_000, 12_000_000)}),
    "Voyage": (0.06, {"Frais médicaux": (100_000, 6_000_000), "Perte de bagages": (50_000, 650_000),
                      "Rapatriement": (1_500_000, 9_000_000)}),
}
VILLES = ["Ouagadougou", "Bobo-Dioulasso", "Koudougou", "Banfora", "Fada N'Gourma", "Ouahigouya"]
CANAUX = ["Agent général", "Courtier", "Bancassurance", "Agence directe"]
STATUTS = ["Réglé", "Réglé", "Réglé", "En expertise", "Offre envoyée", "En cours d'instruction", "Classé sans suite"]


def main(n: int = 400) -> Path:
    out = Path(__file__).with_name("sinistres_2025.csv")
    names = list(BRANCHES)
    weights = [BRANCHES[b][0] for b in names]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["numero", "date_survenance", "date_declaration", "branche", "nature", "ville",
                    "canal", "montant_estime_fcfa", "montant_regle_fcfa", "statut"])
        for i in range(1, n + 1):
            branche = random.choices(names, weights)[0]
            nature, (lo, hi) = random.choice(list(BRANCHES[branche][1].items()))
            surv = date(2025, 1, 1) + timedelta(days=random.randint(0, 364))
            decl = surv + timedelta(days=random.choice([0, 1, 1, 2, 3, 4, 5, 7, 12]))
            estime = int(round(lo + (hi - lo) * random.betavariate(1.3, 4), -3))
            statut = random.choice(STATUTS)
            regle = int(round(estime * random.uniform(0.7, 1.0), -3)) if statut == "Réglé" else 0
            w.writerow([f"SIN-2025-{i:04d}", surv.isoformat(), decl.isoformat(), branche, nature,
                        random.choice(VILLES), random.choice(CANAUX), estime, regle, statut])
    return out


if __name__ == "__main__":
    print(f"Fichier écrit : {main()}")
