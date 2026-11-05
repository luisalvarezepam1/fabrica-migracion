using System.Globalization;

namespace Plantilla.Api.Plataforma;

/// <summary>Hora del negocio (America/Santo_Domingo). En modo demo acepta una hora simulada ISO 8601.</summary>
public static class Reloj
{
    public static readonly TimeZoneInfo Zona = TimeZoneInfo.FindSystemTimeZoneById("America/Santo_Domingo");

    public static DateTimeOffset Ahora(string? simulada = null)
    {
        if (!string.IsNullOrWhiteSpace(simulada))
        {
            if (!DateTimeOffset.TryParse(simulada, CultureInfo.InvariantCulture, DateTimeStyles.None, out var dt))
                throw new ErrorApi("VALIDACION", "X-Demo-Ahora debe ser una fecha ISO 8601.", 400);
            return TimeZoneInfo.ConvertTime(dt, Zona);
        }
        return TimeZoneInfo.ConvertTime(DateTimeOffset.UtcNow, Zona);
    }
}
