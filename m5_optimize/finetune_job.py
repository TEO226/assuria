"""Lance et suit un job de fine-tuning (payant : supprimer le déploiement après usage).

python -m m5_optimize.build_finetune_dataset
python -m m5_optimize.finetune_job [--base-model gpt-4.1-mini-2025-04-14]
python -m m5_optimize.finetune_job --status <job_id>
"""
import argparse
import time

from common.config import DATA, get_openai_client


def wait_for_import(client, file_id: str, label: str) -> None:
    # Azure importe les fichiers de façon asynchrone ; le job échoue tant que l'import n'est pas fini.
    while (status := client.files.retrieve(file_id).status) not in ("processed", "error"):
        print(f"  import {label} : {status}")
        time.sleep(10)
    if status == "error":
        raise SystemExit(f"Import {label} en échec : vérifier le format JSONL.")


def launch(base_model: str) -> None:
    client = get_openai_client()
    ids = {}
    for split in ("train", "valid"):
        with (DATA / f"finetune_{split}.jsonl").open("rb") as f:
            ids[split] = client.files.create(file=f, purpose="fine-tune").id
        print(f"{split} : {ids[split]}")
    for split, file_id in ids.items():
        wait_for_import(client, file_id, split)

    job = client.fine_tuning.jobs.create(model=base_model, training_file=ids["train"],
                                         validation_file=ids["valid"], suffix="assuria")
    print(f"Job : {job.id} ({job.status})")
    watch(job.id)


def watch(job_id: str) -> None:
    client = get_openai_client()
    while True:
        job = client.fine_tuning.jobs.retrieve(job_id)
        print(f"  {job.status}")
        if job.status in ("succeeded", "failed", "cancelled"):
            break
        time.sleep(60)
    if job.status == "succeeded":
        print(f"Modèle : {job.fine_tuned_model}")
        print("Déployer depuis le portail (Fine-tuning > job > Déployer), "
              "puis renseigner FINETUNED_MODEL_DEPLOYMENT dans .env.")
    else:
        print(f"Échec : {getattr(job, 'error', None)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", default="gpt-4.1-mini-2025-04-14")
    parser.add_argument("--status", help="identifiant d'un job existant")
    args = parser.parse_args()
    watch(args.status) if args.status else launch(args.base_model)


if __name__ == "__main__":
    main()
