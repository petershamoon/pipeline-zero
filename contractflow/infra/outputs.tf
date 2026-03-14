output "resource_prefix" {
  description = "Naming prefix for all resources in this stack."
  value       = module.platform.resource_prefix
}

output "resource_names" {
  description = "Canonical resource names by component."
  value       = module.platform.resource_names
}

output "app_settings_contract" {
  description = "Required app settings and secret references for deploy workflows."
  value       = module.platform.app_settings_contract
  sensitive   = true
}

output "backend_fqdn" {
  description = "Backend container app FQDN."
  value       = module.platform.backend_fqdn
}

output "frontend_fqdn" {
  description = "Frontend container app FQDN."
  value       = module.platform.frontend_fqdn
}

output "backend_identity_principal_id" {
  description = "Backend managed identity principal ID for role assignments."
  value       = module.platform.backend_identity_principal_id
}

output "backend_identity_client_id" {
  description = "Backend managed identity client ID for app config."
  value       = module.platform.backend_identity_client_id
}

output "key_vault_uri" {
  description = "Key Vault URI."
  value       = module.platform.key_vault_uri
}

output "acr_login_server" {
  description = "ACR login server."
  value       = module.platform.acr_login_server
}

output "postgres_fqdn" {
  description = "PostgreSQL server FQDN."
  value       = module.platform.postgres_fqdn
}

output "redis_hostname" {
  description = "Redis cache hostname."
  value       = module.platform.redis_hostname
}

output "storage_primary_blob_endpoint" {
  description = "Storage account primary blob endpoint."
  value       = module.platform.storage_primary_blob_endpoint
}
