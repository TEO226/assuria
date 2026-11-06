"""Crée le vector store à partir de data/docs/ et enregistre VECTOR_STORE_ID dans .env.

python -m m4_tools.setup_vector_store
"""
from common.config import DATA, get_openai_client, save_env_value


def main() -> None:
    client = get_openai_client()
    store = client.vector_stores.create(name="assuria-documents-kene")
    print(f"Vector store : {store.id}")

    for path in sorted((DATA / "docs").glob("*.md")):
        with path.open("rb") as f:
            result = client.vector_stores.files.upload_and_poll(vector_store_id=store.id, file=f)
        print(f"  {path.name} : {result.status}")

    save_env_value("VECTOR_STORE_ID", store.id)
    print("VECTOR_STORE_ID enregistré dans .env")


if __name__ == "__main__":
    main()
