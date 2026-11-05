# Plantilla de la raíz de Terraform del destino. La fábrica la copia a destino/infra/ y solo
# ajusta las variables marcadas con «AJUSTAR». El módulo se consume por etiqueta (versión fija).

terraform {
  required_version = ">= 1.9"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.14"
    }
  }
  backend "azurerm" {} # se configura en el pipeline con -backend-config
}

provider "azurerm" {
  features {}
  use_oidc                        = true
  storage_use_azuread             = true
  resource_provider_registrations = "none"
}

data "azurerm_client_config" "actual" {}

locals {
  sufijo = substr(sha1(data.azurerm_client_config.actual.subscription_id), 0, 6)
}

module "app" {
  source = "git::https://github.com/luisalvarezepam1/fabrica-migracion.git//plataforma/terraform/modulos/app-service-linux?ref=modulo-app-service-v1"

  nombre              = "banconet-${local.sufijo}" # AJUSTAR: nombre base de la app
  resource_group_name = "rg-fabrica-net"           # AJUSTAR: grupo de recursos asignado por plataforma
  stack               = "dotnet"                   # AJUSTAR: stack del catálogo
  sku                 = "S1"
  slot_staging        = true
  health_check_path   = "/api/salud"
  app_settings = { # AJUSTAR: configuración sin secretos
    DATABASE_PATH = "/home/data/transferencias.db"
    DEMO_MODE     = "1"
  }
  tags = { app = "banco-transferencias-net" }
}

output "app_name" {
  value = module.app.app_name
}

output "url" {
  value = module.app.url
}

output "url_staging" {
  value = module.app.url_staging
}
