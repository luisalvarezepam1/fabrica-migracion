variable "nombre" {
  description = "Nombre base de los recursos (minúsculas, números y guiones; máximo 40)."
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]{3,40}$", var.nombre))
    error_message = "nombre: solo minúsculas, números y guiones (3 a 40)."
  }
}

variable "resource_group_name" {
  description = "Grupo de recursos existente (lo crea plataforma, no la fábrica)."
  type        = string
}

variable "location" {
  type    = string
  default = "eastus2"
}

variable "stack" {
  description = "Stack del catálogo: dotnet | java | python."
  type        = string
  validation {
    condition     = contains(["dotnet", "java", "python"], var.stack)
    error_message = "stack debe ser dotnet, java o python (ver catalogo/stacks.md)."
  }
}

variable "sku" {
  description = "Plan de App Service. S1 o superior para tener slot de staging."
  type        = string
  default     = "S1"
  validation {
    condition     = contains(["B1", "S1", "P0v3", "P1v3"], var.sku)
    error_message = "sku permitido: B1, S1, P0v3 o P1v3."
  }
}

variable "slot_staging" {
  description = "Crea el slot de staging para despliegue blue/green (requiere S1 o superior)."
  type        = bool
  default     = true
}

variable "health_check_path" {
  type    = string
  default = "/api/salud"
}

variable "comando_inicio" {
  description = "Comando de inicio (vacío para el predeterminado del stack)."
  type        = string
  default     = null
}

variable "app_settings" {
  description = "Configuración de la app. Nunca secretos: usa Key Vault o identidad administrada."
  type        = map(string)
  default     = {}
}

variable "tags" {
  type    = map(string)
  default = {}
}
