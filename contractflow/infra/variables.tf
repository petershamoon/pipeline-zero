variable "project_name" {
  type        = string
  description = "Project prefix used in naming."
  default     = "cf"
}

variable "environment" {
  type        = string
  description = "Deployment environment short code."
  validation {
    condition     = contains(["stg", "prd"], var.environment)
    error_message = "environment must be one of: stg, prd."
  }
}

variable "location" {
  type        = string
  description = "Azure region short name, e.g. eastus2."
}

variable "sequence_number" {
  type        = string
  description = "Two-digit sequence token for globally unique names."
  validation {
    condition     = can(regex("^[0-9]{2}$", var.sequence_number))
    error_message = "sequence_number must be exactly two digits."
  }
}

variable "tags" {
  type        = map(string)
  description = "Required baseline resource tags."
  default = {
    project             = "contractflow"
    managed_by          = "terraform"
    owner               = "manus"
    data_classification = "internal"
  }
}

variable "allowed_frontend_origins" {
  type        = list(string)
  description = "CORS allowlist for backend API."
}

variable "backend_image" {
  type        = string
  description = "Backend image reference in ACR."
}

variable "frontend_image" {
  type        = string
  description = "Frontend image reference in ACR."
}

variable "entra_tenant_id" {
  type        = string
  description = "Microsoft Entra tenant ID."
}

variable "entra_client_id" {
  type        = string
  description = "Microsoft Entra app/client ID."
}

variable "entra_audience" {
  type        = string
  description = "Expected API audience for JWT validation."
}

variable "postgres_admin_password" {
  type        = string
  description = "PostgreSQL administrator password."
  sensitive   = true
}

variable "db_app_password" {
  type        = string
  description = "Application-level DB password / CSRF secret seed."
  sensitive   = true
}
