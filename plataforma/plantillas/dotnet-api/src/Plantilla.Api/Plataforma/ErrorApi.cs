using System.Text.Json;

namespace Plantilla.Api.Plataforma;

/// <summary>Error de negocio o de validación con el sobre del contrato: {"error":{"codigo","mensaje"}}.</summary>
public sealed class ErrorApi(string codigo, string mensaje, int estadoHttp = 422) : Exception(mensaje)
{
    public string Codigo { get; } = codigo;
    public int EstadoHttp { get; } = estadoHttp;
}

public static class ErroresApi
{
    private static readonly JsonSerializerOptions Json = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };

    public static IResult Respuesta(string codigo, string mensaje, int estado) =>
        Results.Json(new { error = new { codigo, mensaje } }, Json, statusCode: estado);

    /// <summary>ErrorApi -> JSON con su código; 404 y 405 bajo /api -> JSON NO_ENCONTRADO / METODO_NO_PERMITIDO.
    /// También agrega a toda respuesta las cabeceras de seguridad del estándar bancario:
    /// X-Content-Type-Options: nosniff y Cache-Control: no-store (no guardar saldos ni datos de cuenta en caché).</summary>
    public static IApplicationBuilder UseErroresApi(this IApplicationBuilder app)
    {
        app.Use(async (ctx, next) =>
        {
            ctx.Response.OnStarting(() =>
            {
                ctx.Response.Headers.TryAdd("X-Content-Type-Options", "nosniff");
                ctx.Response.Headers.TryAdd("Cache-Control", "no-store");
                return Task.CompletedTask;
            });
            try
            {
                await next();
            }
            catch (ErrorApi e)
            {
                ctx.Response.Clear();
                await Respuesta(e.Codigo, e.Message, e.EstadoHttp).ExecuteAsync(ctx);
                return;
            }
            if (!ctx.Response.HasStarted && ctx.Request.Path.StartsWithSegments("/api"))
            {
                if (ctx.Response.StatusCode == 404 && ctx.Response.ContentLength is null or 0)
                    await Respuesta("NO_ENCONTRADO", "Recurso no encontrado.", 404).ExecuteAsync(ctx);
                else if (ctx.Response.StatusCode == 405)
                    await Respuesta("METODO_NO_PERMITIDO", "Método no permitido.", 405).ExecuteAsync(ctx);
            }
        });
        return app;
    }
}
