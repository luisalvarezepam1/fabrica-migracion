---
name: python-a-dotnet
description: Guía de traducción de Python/Flask/SQLite a C# .NET 8 (ASP.NET Core Minimal API + Microsoft.Data.Sqlite) con las trampas que cambian el comportamiento. Úsala al diseñar o escribir el destino .NET.
---
# De Python/Flask a .NET 8

## Equivalencias

| Python / Flask | .NET 8 |
|---|---|
| `Flask` + `Blueprint(url_prefix="/api")` | Minimal API con `app.MapGroup("/api")` |
| `@api.get("/cuentas/<numero>")` | `api.MapGet("/cuentas/{numero}", ...)` |
| `jsonify(obj), 201` | `Results.Json(obj, opciones, statusCode: 201)` |
| `request.headers.get("X")` | `HttpRequest.Headers["X"]` (vacío si no viene) |
| `render_template` + Jinja | Razor Pages o HTML generado; la apariencia puede cambiar, las funciones no |
| `sqlite3` con SQL directo | `Microsoft.Data.Sqlite` con parámetros (`$p`), sin ORM |
| `BEGIN IMMEDIATE` ... `COMMIT` | `connection.BeginTransaction(deferred: false)` (conserva el bloqueo de escritura) |
| `Decimal` + `quantize(ROUND_HALF_UP)` | `decimal` + `Math.Round(x, 0, MidpointRounding.AwayFromZero)` |
| `ZoneInfo("America/Santo_Domingo")` | `TimeZoneInfo.FindSystemTimeZoneById("America/Santo_Domingo")` |
| `datetime.isoformat(timespec="seconds")` | `DateTimeOffset.ToString("yyyy-MM-dd'T'HH:mm:sszzz")` |
| `pytest` | xUnit (`dotnet new xunit`) |

## Trampas que cambian resultados

1. **Redondeo:** `Math.Round(2.5m)` da `2` (redondeo al par). En Python `ROUND_HALF_UP` da `3`. Siempre pasa `MidpointRounding` explícito.
2. **Decimales:** nunca `double` para dinero. `0.0015 * 167000` en `double` no es exacto.
3. **Serialización JSON:** por defecto .NET usa `camelCase`. Si el contrato es `snake_case`, configura `JsonNamingPolicy.SnakeCaseLower` o atributos `[JsonPropertyName]`. Conserva el **orden** de los campos si las pruebas lo comparan.
4. **Importes como texto:** si el origen devuelve `"1670.00"`, el destino también: formatea con `CultureInfo.InvariantCulture` y dos decimales, nunca con la cultura del servidor (que podría usar coma).
5. **Fechas:** el origen devuelve la hora local con desplazamiento (`-04:00`). No devuelvas UTC con `Z` si el contrato no lo hace.
6. **Nulos y campos ausentes:** si el origen devuelve `"fecha_reverso": null`, el destino también debe devolver el campo con `null`, no omitirlo.
7. **Errores:** mismo código HTTP y mismo cuerpo `{"error": {"codigo", "mensaje"}}`. Los 404 y 405 de rutas inexistentes también.
8. **Orden de operaciones en una transacción:** tradúcelo tal cual y luego revisa si tiene sentido (un cobro antes de una validación puede ser un defecto heredado).
9. **SQLite en App Service:** la ruta de la base debe estar en `/home` para que persista; usa la variable `DATABASE_PATH`.

## Estructura sugerida

```
destino/
  Transferencias.sln
  src/Transferencias.Api/        Program.cs, Endpoints/, Dominio/ (reglas), Datos/ (SQL), wwwroot/
  tests/Transferencias.Tests/    pruebas de reglas (comisión, impuesto, límite, idempotencia, reverso)
  infra/                         Terraform (lo pone Plataforma)
  pruebas-contrato/              casos y referencia (lo pone Plataforma)
```
