"""Chat interactif avec tous les outils.

python -m m4_tools.chat_with_tools [--code] [--web]
"""
import argparse

from common.assistant import AssurIA, build_tools
from common.config import DATA, get_openai_client


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", action="store_true", help="charger sinistres_2025.csv dans code_interpreter")
    parser.add_argument("--web", action="store_true", help="activer web_search")
    args = parser.parse_args()

    file_ids = []
    if args.code:
        with (DATA / "sinistres_2025.csv").open("rb") as f:
            file_ids.append(get_openai_client().files.create(file=f, purpose="assistants").id)

    bot = AssurIA(tools=build_tools(code_interpreter=args.code, web_search=args.web, code_file_ids=file_ids))
    print("AssurIA (/reset, /quit)\n")
    while True:
        user = input("Vous : ").strip()
        if user in ("/quit", "/exit"):
            break
        if user == "/reset":
            bot.reset()
            continue
        if not user:
            continue
        turn = bot.ask(user)
        print(f"AssurIA : {turn.text}")
        meta = []
        if turn.tool_calls:
            meta.append("outils : " + ", ".join(turn.tool_calls))
        if turn.citations:
            meta.append("sources : " + ", ".join(turn.citations))
        if turn.files:
            meta.append("fichiers : " + ", ".join(turn.files))
        if meta:
            print("  [" + " | ".join(meta) + "]")
        print()


if __name__ == "__main__":
    main()
