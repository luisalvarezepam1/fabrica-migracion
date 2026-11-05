// Plantilla aprobada (camino dorado) para servicios .NET 8 migrados por la fábrica.
// Ya resuelve: JSON snake_case, sobre de errores {"error":{"codigo","mensaje"}}, 404/405 en JSON bajo /api,
// archivos estáticos en wwwroot (pantalla web en "/"), SQLite por DATABASE_PATH y /api/salud.
// La fábrica agrega el esquema, los datos de ejemplo, las reglas de negocio y los endpoints del módulo.
using System.Text.Json;
using Plantilla.Api.Plataforma;

var builder = WebApplication.CreateBuilder(args);
builder.Services.ConfigureHttpJsonOptions(o =>
{
    o.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower;
    o.SerializerOptions.Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping;
});
builder.Services.AddSingleton(new BaseDeDatos(
    Environment.GetEnvironmentVariable("DATABASE_PATH") ?? Path.Combine(AppContext.BaseDirectory, "datos", "app.db")));

var app = builder.Build();
var modoDemo = (Environment.GetEnvironmentVariable("DEMO_MODE") ?? "1") == "1";

app.UseErroresApi();
app.UseDefaultFiles();
app.UseStaticFiles();

// FÁBRICA: crea el esquema y carga los datos de ejemplo aquí (solo si la base está vacía).
// app.Services.GetRequiredService<BaseDeDatos>().Inicializar(Esquema.Sql, Esquema.CargarSemilla);

var api = app.MapGroup("/api");
api.MapGet("/salud", (HttpRequest req) => Results.Json(new
{
    estado = "ok",
    version = "0.1.0",
    ahora = Reloj.Ahora(modoDemo ? req.Headers["X-Demo-Ahora"].ToString() : null).ToString("yyyy-MM-dd'T'HH:mm:sszzz"),
}));

// FÁBRICA: agrega aquí los endpoints del módulo, por ejemplo:
// api.MapPost("/transferencias", ...);

app.Run();

public partial class Program { }
