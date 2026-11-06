#!/usr/bin/env bash
# Déploie les modèles et attribue le rôle Azure AI User sur une ressource Foundry existante.
#
#   RG=rg-assuria RESOURCE=<ressource-foundry> bash m1_preparation/setup_azure.sh
set -euo pipefail

RG="${RG:?RG non défini}"
RESOURCE="${RESOURCE:?RESOURCE non défini}"
CAPACITY="${CAPACITY:-50}"   # milliers de jetons par minute

deploy () {
  echo "Déploiement $1 ($2 $3)"
  az cognitiveservices account deployment create \
    --resource-group "$RG" --name "$RESOURCE" \
    --deployment-name "$1" --model-name "$2" --model-version "$3" \
    --model-format OpenAI --sku-name GlobalStandard --sku-capacity "$CAPACITY" \
    --output none || echo "  ignoré (existe déjà ou version indisponible)"
}

deploy gpt-4.1-mini gpt-4.1-mini 2025-04-14
deploy gpt-4.1      gpt-4.1      2025-04-14

USER_ID=$(az ad signed-in-user show --query id -o tsv)
SCOPE=$(az cognitiveservices account show -g "$RG" -n "$RESOURCE" --query id -o tsv)
az role assignment create --assignee "$USER_ID" --role "Azure AI User" --scope "$SCOPE" --output none || true

echo "Terminé. Renseigner FOUNDRY_PROJECT_ENDPOINT dans .env (portail > projet > Vue d'ensemble)."
