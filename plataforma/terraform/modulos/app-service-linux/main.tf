# Módulo aprobado ("camino dorado"): App Service Linux con slot de staging, HTTPS, TLS 1.2,
# FTP apagado, health check y Application Insights. La fábrica lo compone; no lo modifica.

terraform {
  required_version = ">= 1.9"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.14"
    }
  }
}

locals {
  stacks = {
    dotnet = { dotnet_version = "8.0", java_version = null, python_version = null, java_server = null, java_server_version = null }
    java   = { dotnet_version = null, java_version = "21", python_version = null, java_server = "JAVA", java_server_version = "21" }
    python = { dotnet_version = null, java_version = null, python_version = "3.12", java_server = null, java_server_version = null }
  }
  stack = local.stacks[var.stack]
  tags  = merge({ gestionado_por = "fabrica-migracion", datos = "ficticios" }, var.tags)
  base_settings = merge({
    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.ai.connection_string
    WEBSITES_ENABLE_APP_SERVICE_STORAGE   = "true"
  }, var.app_settings)
}

resource "azurerm_log_analytics_workspace" "log" {
  name                = "log-${var.nombre}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.tags
}

resource "azurerm_application_insights" "ai" {
  name                = "appi-${var.nombre}"
  resource_group_name = var.resource_group_name
  location            = var.location
  workspace_id        = azurerm_log_analytics_workspace.log.id
  application_type    = "web"
  tags                = local.tags
}

resource "azurerm_service_plan" "plan" {
  name                = "asp-${var.nombre}"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = var.sku
  tags                = local.tags
}

resource "azurerm_linux_web_app" "app" {
  name                = "app-${var.nombre}"
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.plan.id
  https_only          = true
  tags                = local.tags

  site_config {
    always_on                         = true
    ftps_state                        = "Disabled"
    minimum_tls_version               = "1.2"
    health_check_path                 = var.health_check_path
    health_check_eviction_time_in_min = 10
    app_command_line                  = var.comando_inicio
    application_stack {
      dotnet_version      = local.stack.dotnet_version
      java_version        = local.stack.java_version
      java_server         = local.stack.java_server
      java_server_version = local.stack.java_server_version
      python_version      = local.stack.python_version
    }
  }

  app_settings = local.base_settings
}

resource "azurerm_linux_web_app_slot" "staging" {
  count          = var.slot_staging ? 1 : 0
  name           = "staging"
  app_service_id = azurerm_linux_web_app.app.id
  https_only     = true
  tags           = local.tags

  site_config {
    always_on                         = true
    ftps_state                        = "Disabled"
    minimum_tls_version               = "1.2"
    health_check_path                 = var.health_check_path
    health_check_eviction_time_in_min = 10
    app_command_line                  = var.comando_inicio
    application_stack {
      dotnet_version      = local.stack.dotnet_version
      java_version        = local.stack.java_version
      java_server         = local.stack.java_server
      java_server_version = local.stack.java_server_version
      python_version      = local.stack.python_version
    }
  }

  app_settings = local.base_settings
}
