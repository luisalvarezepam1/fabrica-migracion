using Microsoft.Data.Sqlite;

namespace Plantilla.Api.Plataforma;

/// <summary>SQLite con SQL parametrizado (sin ORM). La ruta viene de DATABASE_PATH.</summary>
public sealed class BaseDeDatos(string ruta)
{
    public string Ruta { get; } = ruta;

    public SqliteConnection Abrir()
    {
        var dir = Path.GetDirectoryName(Path.GetFullPath(Ruta));
        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
        var cn = new SqliteConnection(new SqliteConnectionStringBuilder { DataSource = Ruta, DefaultTimeout = 10 }.ToString());
        cn.Open();
        return cn;
    }

    /// <summary>Ejecuta el esquema (CREATE TABLE IF NOT EXISTS ...) y, si la base está vacía, la semilla.</summary>
    public void Inicializar(string esquemaSql, Action<SqliteConnection> cargarSemilla, string tablaControl)
    {
        using var cn = Abrir();
        using (var cmd = cn.CreateCommand()) { cmd.CommandText = esquemaSql; cmd.ExecuteNonQuery(); }
        using var cuenta = cn.CreateCommand();
        cuenta.CommandText = $"SELECT COUNT(*) FROM {tablaControl}";
        if (Convert.ToInt64(cuenta.ExecuteScalar()) == 0) cargarSemilla(cn);
    }
}
