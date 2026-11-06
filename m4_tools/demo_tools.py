"""Un scénario par outil : file_search, function (x2), code_interpreter, web_search (--web).

python -m m4_tools.demo_tools [--web]
"""
import argparse

from common.assistant import AssurIA, build_tools
from common.config import DATA, get_openai_client


def show(title: str, bot: AssurIA, question: str) -> None:
    print(f"\n== {title} ==\n> {question}")
    turn = bot.ask(question)
    print(turn.text)
    if turn.tool_calls:
        print(f"outils : {', '.join(turn.tool_calls)}")
    if turn.citations:
        print(f"sources : {', '.join(turn.citations)}")
    if turn.files:
        print(f"fichiers : {', '.join(turn.files)}")


def upload_claims() -> str:
    csv_path = DATA / "sinistres_2025.csv"
    if not csv_path.exists():
        from data.generate_sinistres_csv import main as generate
        generate()
    with csv_path.open("rb") as f:
        return get_openai_client().files.create(file=f, purpose="assistants").id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web", action="store_true")
    args = parser.parse_args()

    bot = AssurIA(tools=build_tools(file_search=True, functions=False))
    show("file_search", bot, "Quelles sont les exclusions principales de Kéné Habitat ?")

    bot = AssurIA(tools=build_tools(file_search=False, functions=True))
    show("function : prime", bot,
         "Combien coûte une assurance Tiers étendu pour une voiture de 6 CV à usage privé à Ouagadougou, "
         "valeur 6 000 000 FCFA, 4 ans, bonus 0,80 ?")
    bot.reset()
    show("function : sinistre", bot, "Où en est mon dossier SIN-2026-0101 ?")

    bot = AssurIA(tools=build_tools(file_search=False, functions=False, code_interpreter=True,
                                    code_file_ids=[upload_claims()]),
                  max_output_tokens=1500)
    show("code_interpreter", bot,
         "Analyse le fichier des sinistres 2025 : nombre et montant estimé total par branche, "
         "délai moyen de déclaration, puis trace un histogramme du montant estimé par mois "
         "et enregistre-le en PNG.")

    if args.web:
        bot = AssurIA(tools=build_tools(file_search=False, functions=False, web_search=True))
        show("web_search", bot, "Quelles sont les dernières actualités publiées par la CIMA sur l'assurance automobile ?")


if __name__ == "__main__":
    main()
