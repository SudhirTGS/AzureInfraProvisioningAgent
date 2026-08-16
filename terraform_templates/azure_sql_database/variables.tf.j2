variable "resource_group" {
  type        = string
  description = "Existing resource group name. Treated as pre-existing (see main.tf)."
}

variable "region" {
  type        = string
  description = "Azure region, e.g. eastus."
}

variable "sql_server_name" {
  type        = string
  description = "Name of the Azure SQL logical server."
}

variable "database_name" {
  type        = string
  description = "Name of the SQL database."
}

variable "edition" {
  type        = string
  description = "Azure SQL edition. Informational — service_objective (sku_name) is what actually drives the deployed tier."
}

variable "service_objective" {
  type        = string
  description = "Compute/service tier, e.g. GP_Gen5_4, S0, BC_Gen5_2, HS_Gen5_2, Basic. Maps directly to azurerm_mssql_database.sku_name."
}

variable "license_type" {
  type        = string
  description = "LicenseIncluded or BasePrice (Azure Hybrid Benefit)."
}

variable "environment_tag" {
  type        = string
  description = "dev / test / staging / prod — applied as a tag for cost tracking and policy compliance."
}

variable "max_size_gb" {
  type    = number
  default = 32
}

variable "backup_redundancy" {
  type    = string
  default = "Local"
}

variable "sql_admin_login" {
  type        = string
  default     = "sqladmin"
  description = "SQL authentication admin login name for the server."
}

# Never set via chat or tfvars — sensitive. Supply at apply time via the
# TF_VAR_sql_admin_password environment variable. Terraform will error if
# this is left unset when applying.
variable "sql_admin_password" {
  type        = string
  sensitive   = true
  description = "SQL authentication admin password. Supply via TF_VAR_sql_admin_password at apply time — never commit this to tfvars or chat."
}

variable "firewall_rules" {
  type = list(object({
    name              = string
    start_ip_address  = string
    end_ip_address    = string
  }))
  default     = []
  description = "Each rule needs name, start_ip_address, end_ip_address."
}
