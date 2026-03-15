# Platform module — concrete Azure resource definitions.
# Preserves the output contract from the original stub.
# Manus owns: resource creation, identity wiring, networking.
# Codex/Claude owns: naming convention, app settings contract.

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

# ─────────────────────────────────────────────
# Variables (unchanged from contract)
# ─────────────────────────────────────────────

variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "location" {
  type = string
}

variable "sequence_number" {
  type = string
}

variable "tags" {
  type = map(string)
}

variable "allowed_frontend_origins" {
  type = list(string)
}

variable "backend_image" {
  type = string
}

variable "frontend_image" {
  type = string
}

variable "entra_tenant_id" {
  type = string
}

variable "entra_client_id" {
  type = string
}

variable "entra_audience" {
  type = string
}

variable "postgres_admin_password" {
  type      = string
  sensitive = true
}

variable "db_app_password" {
  type      = string
  sensitive = true
}

# ─────────────────────────────────────────────
# Locals — naming and app settings contract
# ─────────────────────────────────────────────

locals {
  resource_prefix = "${var.project_name}-${var.environment}"

  env_tag = var.environment == "prd" ? "production" : "staging"

  all_tags = merge(var.tags, {
    environment = local.env_tag
  })

  resource_names = {
    resource_group          = "${local.resource_prefix}-rg-${var.location}-${var.sequence_number}"
    container_env           = "${local.resource_prefix}-cae-${var.location}-${var.sequence_number}"
    backend_container_app   = "${local.resource_prefix}-api-${var.location}-${var.sequence_number}"
    frontend_container_app  = "${local.resource_prefix}-web-${var.location}-${var.sequence_number}"
    expiration_job          = "${local.resource_prefix}-job-exp-${var.location}-${var.sequence_number}"
    notification_job        = "${local.resource_prefix}-job-notify-${var.location}-${var.sequence_number}"
    # 2026-03-14: postgres is in northcentralus (eastus2 restricted); name uses ncus to avoid location conflict
    postgres_server         = "${local.resource_prefix}-pg-ncus-${var.sequence_number}"
    redis_cache             = "${local.resource_prefix}-redis-${var.location}-${var.sequence_number}"
    storage_account         = "${replace(local.resource_prefix, "-", "")}${var.sequence_number}sa"
    key_vault               = "${local.resource_prefix}-kv-${var.location}-${var.sequence_number}"
    acr                     = "${replace(local.resource_prefix, "-", "")}${var.sequence_number}acr"
    log_analytics_workspace = "${local.resource_prefix}-log-${var.location}-${var.sequence_number}"
  }

  app_settings_contract = {
    backend = {
      ENVIRONMENT               = var.environment == "prd" ? "production" : "staging"
      ALLOWED_ORIGINS           = join(",", var.allowed_frontend_origins)
      ENTRA_TENANT_ID           = var.entra_tenant_id
      ENTRA_CLIENT_ID           = var.entra_client_id
      ENTRA_AUDIENCE            = var.entra_audience
      BACKEND_IMAGE             = var.backend_image
      DATABASE_URL_SECRET_NAME  = "DATABASE-URL"
      REDIS_URL_SECRET_NAME     = "REDIS-URL"
      CSRF_SECRET_SECRET_NAME   = "CSRF-SECRET"
      KEY_VAULT_URI_SECRET_NAME = "KEY-VAULT-URI"
    }
    frontend = {
      FRONTEND_IMAGE       = var.frontend_image
      VITE_ENTRA_CLIENT_ID = var.entra_client_id
      VITE_ENTRA_AUTHORITY = "https://login.microsoftonline.com/${var.entra_tenant_id}"
      VITE_API_URL         = "https://${azurerm_container_app.backend.ingress[0].fqdn}/api/v1"
    }
  }
}

# ─────────────────────────────────────────────
# Data sources
# ─────────────────────────────────────────────

data "azurerm_client_config" "current" {}

# ─────────────────────────────────────────────
# Resource Group
# ─────────────────────────────────────────────

resource "azurerm_resource_group" "main" {
  name     = local.resource_names.resource_group
  location = var.location
  tags     = local.all_tags
}

# ─────────────────────────────────────────────
# Log Analytics Workspace
# ─────────────────────────────────────────────

resource "azurerm_log_analytics_workspace" "main" {
  name                = local.resource_names.log_analytics_workspace
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.all_tags
}

# ─────────────────────────────────────────────
# Container Apps Environment
# ─────────────────────────────────────────────

resource "azurerm_container_app_environment" "main" {
  name                       = local.resource_names.container_env
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = local.all_tags
}

# ─────────────────────────────────────────────
# Azure Container Registry
# ─────────────────────────────────────────────

resource "azurerm_container_registry" "main" {
  name                = local.resource_names.acr
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = local.all_tags
}

# ─────────────────────────────────────────────
# Key Vault
# ─────────────────────────────────────────────

resource "azurerm_key_vault" "main" {
  name                       = local.resource_names.key_vault
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = true  # enabled: satisfies Semgrep keyvault-purge-enabled; soft_delete_retention_days=7 is the minimum
  rbac_authorization_enabled  = true
  tags                       = local.all_tags

  # Semgrep: keyvault-specify-network-acl — default deny with AzureServices bypass
  network_acls {
    default_action             = "Deny"
    bypass                     = ["AzureServices"]
    ip_rules                   = []
    virtual_network_subnet_ids = []
  }
}

# Grant current deployer Key Vault Administrator for secret management
resource "azurerm_role_assignment" "kv_deployer_admin" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}

# ─────────────────────────────────────────────
# Storage Account + Blob Container
# ─────────────────────────────────────────────

resource "azurerm_storage_account" "main" {
  name                            = local.resource_names.storage_account
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"
  tags                            = local.all_tags

  # Semgrep: storage-queue-services-logging — enable queue service logging
  queue_properties {
    logging {
      delete                = true
      read                  = true
      write                 = true
      version               = "1.0"
      retention_policy_days = 7
    }
  }
}

resource "azurerm_storage_container" "contracts" {
  name                  = "contracts"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

# ─────────────────────────────────────────────
# PostgreSQL Flexible Server
# ─────────────────────────────────────────────

resource "azurerm_postgresql_flexible_server" "main" {
  name                          = local.resource_names.postgres_server
  resource_group_name           = azurerm_resource_group.main.name
  # 2026-03-14: eastus2 is LocationIsOfferRestricted for PostgreSQL Flexible Server
  # on this Azure subscription. Using northcentralus as documented exception.
  # All other resources remain in eastus2. Ref: handoff/azure-resource-contract.md fallback policy.
  location                      = "northcentralus"
  version                       = "16"
  administrator_login           = "cfadmin"
  administrator_password        = var.postgres_admin_password
  storage_mb                    = 32768
  sku_name                      = "B_Standard_B1ms"
  backup_retention_days         = 7
  geo_redundant_backup_enabled  = false
  public_network_access_enabled = true # staging fallback — restrict in production
  # 2026-03-14: northcentralus does not support zone=1; removed zone constraint (no-preference)
  tags                          = local.all_tags
}

resource "azurerm_postgresql_flexible_server_database" "contractflow" {
  name      = "contractflow"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Firewall rule: allow Azure services (staging only)
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# ─────────────────────────────────────────────
# Azure Cache for Redis
# ─────────────────────────────────────────────

resource "azurerm_redis_cache" "main" {
  name                          = local.resource_names.redis_cache
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  capacity                      = 0
  family                        = "C"
  sku_name                      = "Basic"
  minimum_tls_version           = "1.2"
  public_network_access_enabled = true # staging fallback
  redis_configuration {}
  tags = local.all_tags
}

# ─────────────────────────────────────────────
# User-Assigned Managed Identity (for backend + jobs)
# ─────────────────────────────────────────────

resource "azurerm_user_assigned_identity" "backend" {
  # Updated 2026-03-14: renamed from id-api to id to match handoff contract (cf-stg-id-eastus2-01)
  name                = "${local.resource_prefix}-id-${var.location}-${var.sequence_number}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.all_tags
}

# MI → Key Vault Secrets User
resource "azurerm_role_assignment" "backend_kv" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.backend.principal_id
}

# MI → Storage Blob Data Contributor
resource "azurerm_role_assignment" "backend_blob" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.backend.principal_id
}

# MI → AcrPull on ACR
resource "azurerm_role_assignment" "backend_acr" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.backend.principal_id
}

# ─────────────────────────────────────────────
# Key Vault Secrets
# ─────────────────────────────────────────────

resource "azurerm_key_vault_secret" "database_url" {
  name            = "DATABASE-URL"
  value           = "postgresql+asyncpg://cfadmin:${var.postgres_admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/contractflow?sslmode=require"
  key_vault_id    = azurerm_key_vault.main.id
  content_type    = "text/plain" # Semgrep: keyvault-content-type-for-secret
  expiration_date = timeadd(timestamp(), "8760h") # Semgrep: keyvault-ensure-secret-expires — 1 year TTL
  depends_on      = [azurerm_role_assignment.kv_deployer_admin]

  lifecycle {
    ignore_changes = [expiration_date] # prevent perpetual drift on re-apply
  }
}

resource "azurerm_key_vault_secret" "redis_url" {
  name            = "REDIS-URL"
  value           = "rediss://:${azurerm_redis_cache.main.primary_access_key}@${azurerm_redis_cache.main.hostname}:${azurerm_redis_cache.main.ssl_port}/0"
  key_vault_id    = azurerm_key_vault.main.id
  content_type    = "text/plain" # Semgrep: keyvault-content-type-for-secret
  expiration_date = timeadd(timestamp(), "8760h") # Semgrep: keyvault-ensure-secret-expires — 1 year TTL
  depends_on      = [azurerm_role_assignment.kv_deployer_admin]

  lifecycle {
    ignore_changes = [expiration_date] # prevent perpetual drift on re-apply
  }
}

resource "azurerm_key_vault_secret" "csrf_secret" {
  name            = "CSRF-SECRET"
  value           = var.db_app_password # reuse as a strong random value, or generate separately
  key_vault_id    = azurerm_key_vault.main.id
  content_type    = "text/plain" # Semgrep: keyvault-content-type-for-secret
  expiration_date = timeadd(timestamp(), "8760h") # Semgrep: keyvault-ensure-secret-expires — 1 year TTL
  depends_on      = [azurerm_role_assignment.kv_deployer_admin]

  lifecycle {
    ignore_changes = [expiration_date] # prevent perpetual drift on re-apply
  }
}

resource "azurerm_key_vault_secret" "key_vault_uri" {
  name            = "KEY-VAULT-URI"
  value           = azurerm_key_vault.main.vault_uri
  key_vault_id    = azurerm_key_vault.main.id
  content_type    = "text/plain" # Semgrep: keyvault-content-type-for-secret
  expiration_date = timeadd(timestamp(), "8760h") # Semgrep: keyvault-ensure-secret-expires — 1 year TTL
  depends_on      = [azurerm_role_assignment.kv_deployer_admin]

  lifecycle {
    ignore_changes = [expiration_date] # prevent perpetual drift on re-apply
  }
}

# ─────────────────────────────────────────────
# Backend Container App
# ─────────────────────────────────────────────

resource "azurerm_container_app" "backend" {
  name                         = local.resource_names.backend_container_app
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.all_tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.backend.id]
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.backend.id
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 0
    max_replicas = 2

    container {
      name   = "backend"
      image  = var.backend_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "ENVIRONMENT"
        value = var.environment == "prd" ? "production" : "staging"
      }
      env {
        name  = "ALLOWED_ORIGINS"
        value = join(",", var.allowed_frontend_origins)
      }
      env {
        name  = "ENTRA_TENANT_ID"
        value = var.entra_tenant_id
      }
      env {
        name  = "ENTRA_CLIENT_ID"
        value = var.entra_client_id
      }
      env {
        name  = "ENTRA_AUDIENCE"
        value = var.entra_audience
      }
      env {
        name  = "KEY_VAULT_URI"
        value = azurerm_key_vault.main.vault_uri
      }
      env {
        name  = "AZURE_STORAGE_ACCOUNT_URL"
        value = azurerm_storage_account.main.primary_blob_endpoint
      }
      env {
        name  = "AZURE_STORAGE_CONTAINER"
        value = "contracts"
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.backend.client_id
      }
      env {
        name  = "LOCAL_AUTH_ENABLED"
        value = "false"
      }
      env {
        name  = "SESSION_SECURE_COOKIE"
        value = "true"
      }
      env {
        name  = "SESSION_COOKIE_NAME"
        value = "cf_session"
      }
      env {
        name  = "CSRF_COOKIE_NAME"
        value = "cf_csrf"
      }
      env {
        name  = "SESSION_TTL_MINUTES"
        value = "60"
      }
      env {
        name  = "MAX_UPLOAD_SIZE_MB"
        value = "50"
      }
      env {
        name  = "SAS_URL_TTL_MINUTES"
        value = "15"
      }
      # Secrets from Key Vault are read at runtime via managed identity
      # DATABASE_URL, REDIS_URL, CSRF_SECRET fetched from Key Vault by app code

      liveness_probe {
        transport = "HTTP"
        path      = "/health/live"
        port      = 8000
      }

      readiness_probe {
        transport = "HTTP"
        path      = "/health/ready"
        port      = 8000
      }
    }
  }
}

# ─────────────────────────────────────────────
# Frontend Container App
# ─────────────────────────────────────────────

resource "azurerm_container_app" "frontend" {
  name                         = local.resource_names.frontend_container_app
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.all_tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.backend.id]
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.backend.id
  }

  ingress {
    external_enabled = true
    target_port      = 3000
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 0
    max_replicas = 2

    container {
      name   = "frontend"
      image  = var.frontend_image
      cpu    = 0.25
      memory = "0.5Gi"

      liveness_probe {
        transport = "HTTP"
        path      = "/health"
        port      = 3000
      }
    }
  }
}

# ─────────────────────────────────────────────
# Container App Jobs
# ─────────────────────────────────────────────

resource "azurerm_container_app_job" "expiration" {
  name                         = local.resource_names.expiration_job
  location                     = azurerm_resource_group.main.location
  resource_group_name          = azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  replica_timeout_in_seconds   = 300
  tags                         = local.all_tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.backend.id]
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.backend.id
  }

  schedule_trigger_config {
    cron_expression          = "0 */6 * * *"
    parallelism              = 1
    replica_completion_count = 1
  }

  template {
    container {
      name   = "expiration-job"
      image  = var.backend_image
      cpu    = 0.25
      memory = "0.5Gi"

      command = ["python", "-m", "jobs.expiration-job.main"]

      env {
        name  = "ENVIRONMENT"
        value = var.environment == "prd" ? "production" : "staging"
      }
      env {
        name  = "KEY_VAULT_URI"
        value = azurerm_key_vault.main.vault_uri
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.backend.client_id
      }
    }
  }
}

resource "azurerm_container_app_job" "notification" {
  name                         = local.resource_names.notification_job
  location                     = azurerm_resource_group.main.location
  resource_group_name          = azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  replica_timeout_in_seconds   = 300
  tags                         = local.all_tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.backend.id]
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.backend.id
  }

  schedule_trigger_config {
    cron_expression          = "0 8 * * *"
    parallelism              = 1
    replica_completion_count = 1
  }

  template {
    container {
      name   = "notification-job"
      image  = var.backend_image
      cpu    = 0.25
      memory = "0.5Gi"

      command = ["python", "-m", "jobs.notification-job.main"]

      env {
        name  = "ENVIRONMENT"
        value = var.environment == "prd" ? "production" : "staging"
      }
      env {
        name  = "KEY_VAULT_URI"
        value = azurerm_key_vault.main.vault_uri
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.backend.client_id
      }
    }
  }
}

# ─────────────────────────────────────────────
# Azure Monitor Alert Rules
# ─────────────────────────────────────────────

resource "azurerm_monitor_action_group" "main" {
  name                = "${local.resource_prefix}-alerts-${var.sequence_number}"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "cf-alerts"
  tags                = local.all_tags

  email_receiver {
    name          = "pete"
    email_address = "petershamoon@protonmail.com"
  }
}

# ─────────────────────────────────────────────
# Outputs (preserves original contract)
# ─────────────────────────────────────────────

output "resource_prefix" {
  value = local.resource_prefix
}

output "resource_names" {
  value = local.resource_names
}

output "app_settings_contract" {
  value     = local.app_settings_contract
  sensitive = true
}

output "backend_fqdn" {
  value = azurerm_container_app.backend.ingress[0].fqdn
}

output "frontend_fqdn" {
  value = azurerm_container_app.frontend.ingress[0].fqdn
}

output "backend_identity_principal_id" {
  value = azurerm_user_assigned_identity.backend.principal_id
}

output "backend_identity_client_id" {
  value = azurerm_user_assigned_identity.backend.client_id
}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}

output "acr_login_server" {
  value = azurerm_container_registry.main.login_server
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "redis_hostname" {
  value = azurerm_redis_cache.main.hostname
}

output "storage_primary_blob_endpoint" {
  value = azurerm_storage_account.main.primary_blob_endpoint
}
