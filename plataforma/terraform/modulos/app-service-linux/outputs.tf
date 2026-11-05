output "app_name" {
  value = azurerm_linux_web_app.app.name
}

output "url" {
  value = "https://${azurerm_linux_web_app.app.default_hostname}"
}

output "url_staging" {
  value = var.slot_staging ? "https://${azurerm_linux_web_app_slot.staging[0].default_hostname}" : null
}

output "resource_group_name" {
  value = var.resource_group_name
}
