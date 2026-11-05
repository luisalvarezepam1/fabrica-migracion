---
name: terraform-camino-dorado
description: Cómo preparar la infraestructura y el CI/CD del destino usando solo los módulos de Terraform y las plantillas de pipeline aprobados por plataforma. Úsala en la etapa de plataforma.
---
# Infraestructura por camino dorado

La fábrica **compone** infraestructura aprobada; no la inventa.

## Piezas aprobadas

- Módulo [`plataforma/terraform/modulos/app-service-linux`](../../../plataforma/terraform/modulos/app-service-linux): App Service Linux con slot `staging`, HTTPS, TLS 1.2, FTP apagado, health check, Log Analytics y Application Insights. Se consume por etiqueta git (`?ref=modulo-app-service-v1`).
- Raíz de ejemplo [`plataforma/terraform/plantilla-raiz/main.tf`](../../../plataforma/terraform/plantilla-raiz/main.tf): se copia a `destino/infra/main.tf` y solo se ajustan las líneas `AJUSTAR`.
- Pipeline [`plataforma/pipelines/dotnet-app-service.yml`](../../../plataforma/pipelines/dotnet-app-service.yml): pruebas → infraestructura → slot staging → pruebas de contrato → **aprobación humana** (environment `produccion`) → swap.

## Reglas

1. No agregues recursos fuera del módulo. Si hace falta algo nuevo, es una decisión de arquitectura (ADR) y un cambio al módulo, fuera de la corrida.
2. Nada de secretos en variables ni en `app_settings`. Autenticación a Azure por OIDC (sin secretos guardados).
3. El grupo de recursos lo asigna plataforma; la fábrica no lo crea.
4. Valida sin credenciales: `terraform init -backend=false`, `terraform validate`, `terraform fmt -check`.
5. **Nunca** `terraform apply` ni `plan` con credenciales desde la fábrica: lo hace el pipeline con su propia puerta.
