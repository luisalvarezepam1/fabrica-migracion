using System.Net;
using System.Text.Json;
using Microsoft.AspNetCore.Mvc.Testing;

namespace Plantilla.Tests;

// Pruebas de la plantilla. La fábrica agrega al lado las pruebas de las reglas del módulo.
public class PlataformaTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _cli;

    public PlataformaTests(WebApplicationFactory<Program> f)
    {
        Environment.SetEnvironmentVariable("DATABASE_PATH", Path.Combine(Path.GetTempPath(), $"plantilla-{Guid.NewGuid():N}.db"));
        _cli = f.CreateClient();
    }

    [Fact]
    public async Task Salud_responde_ok_en_snake_case()
    {
        var r = await _cli.GetAsync("/api/salud");
        Assert.Equal(HttpStatusCode.OK, r.StatusCode);
        var json = JsonDocument.Parse(await r.Content.ReadAsStringAsync()).RootElement;
        Assert.Equal("ok", json.GetProperty("estado").GetString());
    }

    [Fact]
    public async Task Ruta_inexistente_devuelve_error_json()
    {
        var r = await _cli.GetAsync("/api/no-existe");
        Assert.Equal(HttpStatusCode.NotFound, r.StatusCode);
        var json = JsonDocument.Parse(await r.Content.ReadAsStringAsync()).RootElement;
        Assert.Equal("NO_ENCONTRADO", json.GetProperty("error").GetProperty("codigo").GetString());
    }

    [Fact]
    public async Task Toda_respuesta_lleva_cabeceras_de_seguridad()
    {
        foreach (var ruta in new[] { "/api/salud", "/api/no-existe", "/" })
        {
            var r = await _cli.GetAsync(ruta);
            Assert.Equal("nosniff", r.Headers.GetValues("X-Content-Type-Options").Single());
            Assert.Contains("no-store", r.Headers.CacheControl?.ToString() ?? "");
        }
    }

    [Fact]
    public void Sqlite_nativo_abre_y_consulta()
    {
        var db = new Plantilla.Api.Plataforma.BaseDeDatos(Path.Combine(Path.GetTempPath(), $"plantilla-{Guid.NewGuid():N}.db"));
        using var cn = db.Abrir();
        using var cmd = cn.CreateCommand();
        cmd.CommandText = "select sqlite_version()";
        Assert.False(string.IsNullOrEmpty(cmd.ExecuteScalar() as string));
    }
}
