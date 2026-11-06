"""Chat multi-tours avec la Responses API (historique conservé côté service).

python -m m3_chat.chat_responses [--stream]
Commandes : /reset, /quit
"""
import argparse

from common.config import CHAT_MODEL, get_openai_client

INSTRUCTIONS = ("Tu es AssurIA, l'assistant de Kéné Assurances IARD, une compagnie fictive. "
                "Tu réponds en français, avec clarté et concision, aux questions sur l'assurance non-vie. "
                "Si tu n'es pas sûr d'une information propre à la compagnie, dis-le.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", action="store_true")
    args = parser.parse_args()

    client = get_openai_client()
    previous_id = None
    print(f"AssurIA ({CHAT_MODEL}, Responses API)\n")

    while True:
        user = input("Vous : ").strip()
        if user in ("/quit", "/exit"):
            break
        if user == "/reset":
            previous_id = None
            print("(nouvelle conversation)\n")
            continue
        if not user:
            continue

        params = dict(model=CHAT_MODEL, instructions=INSTRUCTIONS, input=user)
        if previous_id:  # Foundry rejette previous_response_id=null
            params["previous_response_id"] = previous_id

        if args.stream:
            print("AssurIA : ", end="", flush=True)
            for event in client.responses.create(**params, stream=True):
                if event.type == "response.created":
                    previous_id = event.response.id
                elif event.type == "response.output_text.delta":
                    print(event.delta, end="", flush=True)
                elif event.type in ("response.failed", "error"):
                    print(f"\n[Erreur : {getattr(event, 'message', None) or event}]")
            print("\n")
        else:
            response = client.responses.create(**params)
            previous_id = response.id
            print(f"AssurIA : {response.output_text}")
            print(f"  [{response.usage.input_tokens} jetons entrée / {response.usage.output_tokens} sortie]\n")


if __name__ == "__main__":
    main()
