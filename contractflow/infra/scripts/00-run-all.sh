#!/usr/bin/env bash
# 00-run-all.sh
# Master orchestration for ContractFlow staging provisioning.
# Run each step individually or all at once.
#
# Usage:
#   cd contractflow/infra
#   source .env.staging
#   ./scripts/00-run-all.sh [step]
#
# Steps:
#   login     - Azure CLI login with service principal
#   entra     - Create Entra app registration (script 01)
#   oidc      - Create GitHub OIDC federation (script 02)
#   terraform - Run terraform init/plan/apply
#   secrets   - Populate GitHub environment secrets (script 03)
#   validate  - Post-deploy validation (script 04)
#   all       - Run all steps in order
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"

step="${1:-all}"

run_login() {
  echo ""
  echo "╔══════════════════════════════════════╗"
  echo "║  STEP: Azure CLI Login               ║"
  echo "╚══════════════════════════════════════╝"
  az login --service-principal \
    -u "$ARM_CLIENT_ID" \
    -p "$ARM_CLIENT_SECRET" \
    --tenant "$ARM_TENANT_ID"
  az account set --subscription "$ARM_SUBSCRIPTION_ID"
  echo "Logged in as $(az account show --query user.name -o tsv)"
}

run_entra() {
  echo ""
  echo "╔══════════════════════════════════════╗"
  echo "║  STEP: Entra App Registration        ║"
  echo "╚══════════════════════════════════════╝"
  bash "$SCRIPT_DIR/01-entra-app-registration.sh"
}

run_oidc() {
  echo ""
  echo "╔══════════════════════════════════════╗"
  echo "║  STEP: GitHub OIDC Federation        ║"
  echo "╚══════════════════════════════════════╝"
  bash "$SCRIPT_DIR/02-github-oidc-federation.sh"
}

run_terraform() {
  echo ""
  echo "╔══════════════════════════════════════╗"
  echo "║  STEP: Terraform Init/Plan/Apply     ║"
  echo "╚══════════════════════════════════════╝"
  cd "$INFRA_DIR"

  echo "--- terraform init ---"
  terraform init

  echo ""
  echo "--- terraform plan ---"
  terraform plan \
    -var-file=envs/staging/terraform.tfvars \
    -var="postgres_admin_password=${TF_VAR_postgres_admin_password}" \
    -var="db_app_password=${TF_VAR_db_app_password}" \
    -out=staging.tfplan

  echo ""
  echo "--- terraform apply ---"
  terraform apply staging.tfplan

  echo ""
  echo "--- terraform output ---"
  terraform output -json > "$INFRA_DIR/staging-outputs.json"
  echo "Outputs saved to staging-outputs.json"
}

run_secrets() {
  echo ""
  echo "╔══════════════════════════════════════╗"
  echo "║  STEP: GitHub Environment Secrets    ║"
  echo "╚══════════════════════════════════════╝"
  bash "$SCRIPT_DIR/03-github-environment-secrets.sh"
}

run_validate() {
  echo ""
  echo "╔══════════════════════════════════════╗"
  echo "║  STEP: Post-Deploy Validation        ║"
  echo "╚══════════════════════════════════════╝"
  bash "$SCRIPT_DIR/04-post-deploy-validation.sh"
}

case "$step" in
  login)     run_login ;;
  entra)     run_entra ;;
  oidc)      run_oidc ;;
  terraform) run_terraform ;;
  secrets)   run_secrets ;;
  validate)  run_validate ;;
  all)
    run_login
    run_entra
    echo ""
    echo ">>> PAUSE: Update .env.staging with ENTRA_APP_CLIENT_ID and ENTRA_APP_OBJECT_ID"
    echo ">>> Then update terraform.tfvars with entra_client_id"
    echo ">>> Press Enter to continue..."
    read -r
    run_oidc
    echo ""
    echo ">>> PAUSE: Update .env.staging with DEPLOY_APP_CLIENT_ID"
    echo ">>> Press Enter to continue..."
    read -r
    run_terraform
    run_secrets
    run_validate
    ;;
  *)
    echo "Unknown step: $step"
    echo "Valid steps: login, entra, oidc, terraform, secrets, validate, all"
    exit 1
    ;;
esac

echo ""
echo "Done."
