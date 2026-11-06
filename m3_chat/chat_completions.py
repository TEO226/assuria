"""Même chat avec ChatCompletions : l'historique est renvoyé à chaque appel.

python -m m3_chat.chat_completions
"""
from common.config import CHAT_MODEL, get_openai_client
from m3_chat.chat_responses import INSTRUCTIONS


def main() -> None:
    client = get_openai_client()
    messages = [{"role": "system", "content": INSTRUCTIONS}]
    print(f"AssurIA ({CHAT_MODEL}, ChatCompletions API)\n")

    while True:
        user = input("Vous : ").strip()
        if user in ("/quit", "/exit"):
            break
        if not user:
            continue
        messages.append({"role": "user", "content": user})
        completion = client.chat.completions.create(model=CHAT_MODEL, messages=messages, temperature=0.3)
        answer = completion.choices[0].message.content
        messages.append({"role": "assistant", "content": answer})
        print(f"AssurIA : {answer}")
        print(f"  [{completion.usage.prompt_tokens} jetons entrée, {len(messages)} messages]\n")


if __name__ == "__main__":
    main()
