"""Vérifie la configuration : .env, authentification, projet Foundry, déploiements.

python -m m1_preparation.check_setup
"""
from common.config import CANDIDATE_MODEL, CHAT_MODEL, EVAL_MODEL, env

OK, KO = "[OK]", "[KO]"


def main() -> None:
    endpoint = env("FOUNDRY_PROJECT_ENDPOINT")
    if not endpoint or "<" in endpoint:
        print(f"{KO} FOUNDRY_PROJECT_ENDPOINT non renseigné")
        return
    print(f"{OK} Point de terminaison : {endpoint}")

    try:
        from common.config import get_credential
        token = get_credential().get_token("https://ai.azure.com/.default")
        print(f"{OK} Authentification Entra ID (expiration {token.expires_on})")
    except Exception as exc:  # noqa: BLE001
        print(f"{KO} Authentification : {exc}  ->  az login")
        return

    from common.config import get_openai_client, get_project_client
    project = get_project_client()

    try:
        deployments = [d.name for d in project.deployments.list()]
        print(f"{OK} Déploiements : {', '.join(deployments) or 'aucun'}")
        for name in sorted({CHAT_MODEL, CANDIDATE_MODEL, EVAL_MODEL}):
            print(f"    {OK if name in deployments else KO} {name}")
    except Exception as exc:  # noqa: BLE001
        print(f"{KO} Déploiements : {exc}  ->  rôle Azure AI User requis")

    try:
        connections = [f"{c.name} ({c.type})" for c in project.connections.list()]
        print(f"{OK} Connexions : {', '.join(connections) or 'aucune'}")
    except Exception as exc:  # noqa: BLE001
        print(f"{KO} Connexions : {exc}")

    try:
        reply = get_openai_client().responses.create(
            model=CHAT_MODEL, input="Réponds uniquement : connexion réussie.", max_output_tokens=20)
        print(f"{OK} {CHAT_MODEL} : {reply.output_text.strip()}")
    except Exception as exc:  # noqa: BLE001
        print(f"{KO} {CHAT_MODEL} : {exc}")


if __name__ == "__main__":
    main()
