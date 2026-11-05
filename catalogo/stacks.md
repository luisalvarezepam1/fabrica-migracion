# Catálogo de stacks

La fábrica solo migra a stacks de este catálogo. Cada stack tiene un módulo de Terraform y una plantilla de pipeline aprobados. Si una solicitud pide otro stack, la fábrica se detiene y lo reporta al líder.

| Id | Estado | Lenguaje y framework | Datos | Hosting | Terraform | Pipeline |
|---|---|---|---|---|---|---|
| `dotnet8-appservice` | **Aprobado** | C# 12 · .NET 8 · ASP.NET Core Minimal API | SQLite con `Microsoft.Data.Sqlite` (sin ORM) o Azure SQL | Azure App Service Linux S1 con slot `staging` | `modulos/app-service-linux` (`stack = "dotnet"`) | `pipelines/dotnet-app-service.yml` |
| `python312-appservice` | Aprobado (stack de origen) | Python 3.12 · Flask 3 · gunicorn | SQLite | Azure App Service Linux B1/S1 | `modulos/app-service-linux` (`stack = "python"`) | — |
| `java21-appservice` | En evaluación | Java 21 · Spring Boot 3 | SQLite/JDBC o Azure SQL | Azure App Service Linux S1 | `modulos/app-service-linux` (`stack = "java"`) | Pendiente: requiere aprobación de arquitectura antes de usarlo |

## Fuera de catálogo

Node.js, Go, contenedores propios, AKS, Azure Functions, bases NoSQL y cualquier otro servicio. Para agregarlos se necesita una decisión de arquitectura (ADR), un módulo aprobado y una plantilla de pipeline.

## Reglas del destino `dotnet8-appservice`

- Se parte de la plantilla aprobada `plataforma/plantillas/dotnet-api` (`fabrica.py destino crear --nombre <Nombre>`).

- Proyecto `src/Transferencias.Api` (o el nombre que fije el Arquitecto) y pruebas en `tests/`.
- Importes en `decimal` o en enteros de centavos. **`Math.Round` por defecto redondea al par**: usa `MidpointRounding.AwayFromZero` cuando la regla de origen sea «mitad hacia arriba».
- Zona horaria con `TimeZoneInfo.FindSystemTimeZoneById("America/Santo_Domingo")` (IANA; funciona en Linux).
- JSON: mismos nombres de campo que el contrato de origen (por ejemplo `snake_case`) y los importes como texto con dos decimales si así los entrega el origen.
- Sin secretos en `appsettings.json`.
