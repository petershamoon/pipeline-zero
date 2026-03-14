# ContractFlow Infrastructure
# Codex/Claude defines module contracts and validation rules.
# Manus owns terraform init/plan/apply in Azure subscriptions.

terraform {
  required_version = ">= 1.9"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # Remote backend for state isolation (uncomment when storage account is ready)
  # backend "azurerm" {
  #   resource_group_name  = "cf-tfstate-rg"
  #   storage_account_name = "cftfstate01"
  #   container_name       = "tfstate"
  #   key                  = "staging.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
  subscription_id = "5a9c39a7-65a6-4e2d-9a2b-25d1ac08ff08"
}

module "platform" {
  source = "./modules/platform"

  project_name             = var.project_name
  environment              = var.environment
  location                 = var.location
  sequence_number          = var.sequence_number
  tags                     = var.tags
  allowed_frontend_origins = var.allowed_frontend_origins

  backend_image  = var.backend_image
  frontend_image = var.frontend_image

  entra_tenant_id = var.entra_tenant_id
  entra_client_id = var.entra_client_id
  entra_audience  = var.entra_audience

  postgres_admin_password = var.postgres_admin_password
  db_app_password         = var.db_app_password
}
