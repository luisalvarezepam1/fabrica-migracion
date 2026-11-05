#!/usr/bin/env python3
"""Utilidades de la fábrica de migración (solo biblioteca estándar).

Uso:
  python3 herramientas/fabrica.py verificar
  python3 herramientas/fabrica.py iniciar solicitudes/<archivo>.md
  python3 herramientas/fabrica.py evento --etapa analisis --agente Analista --tipo artefacto --resumen "..." [--archivo ruta]
  python3 herramientas/fabrica.py puerta --etapa analisis --rol "Líder" --decision aprobado --por "Nombre" --justificacion "..."
  python3 herramientas/fabrica.py estado
  python3 herramientas/fabrica.py replay
  python3 herramientas/fabrica.py costo                         # tokens, créditos y USD por agente (historial local de VS Code)

Servicios (iguales en Windows, macOS y Linux; en Windows usa `python` en lugar de `python3`):
  python3 herramientas/fabrica.py preparar                     # dependencias del origen y paquetes de la plantilla .NET
  python3 herramientas/fabrica.py origen iniciar|salud|detener  # origen en http://127.0.0.1:5050
  python3 herramientas/fabrica.py destino crear --nombre Transferencias   # copia la plantilla aprobada a destino/
  python3 herramientas/fabrica.py destino iniciar|salud|detener # destino en http://127.0.0.1:5080
  python3 herramientas/fabrica.py medir --base http://127.0.0.1:5080 --ruta /api/cuentas
  python3 herramientas/fabrica.py archivar                     # guarda la corrida activa, fuente/ y destino/ en corridas/archivo/

Todo queda en corridas/<id>/: solicitud, estado.json, eventos.jsonl y los artefactos de cada etapa.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import servicios  # noqa: E402
import costo  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CORRIDAS = RAIZ / "corridas"
ACTUAL = CORRIDAS / ".actual"

ETAPAS = [
    ("analisis", "Análisis del requerimiento", "Analista", "Líder solicitante"),
    ("plan", "Plan de trabajo en Jira", "Planificador", None),
    ("arquitectura", "Arquitectura y diseño destino", "Arquitecto", "Arquitecto responsable"),
    ("caracterizacion", "Caracterización del origen", "Caracterizador", "Dueño de negocio"),
    ("migracion", "Migración del código", "Migrador", None),
    ("pruebas", "Pruebas de equivalencia", "Tester", None),
    ("revision", "Revisión de seguridad y dinero", "Revisor", "Riesgo / Seguridad"),
    ("plataforma", "Infraestructura y entrega", "Plataforma", "Comité de cambios (CAB)"),
    ("aprendizaje", "Documentación y replay", "Bibliotecario", None),
]
NOMBRES = {e[0]: e for e in ETAPAS}


def ahora():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def corrida_actual():
    if not ACTUAL.exists():
        sys.exit("No hay una corrida activa. Ejecuta primero: python3 herramientas/fabrica.py iniciar <solicitud.md>")
    return CORRIDAS / ACTUAL.read_text().strip()


def leer_estado(c):
    return json.loads((c / "estado.json").read_text(encoding="utf-8"))


def guardar_estado(c, est):
    (c / "estado.json").write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")


def registrar(c, evento):
    evento = {"ts": ahora(), **evento}
    with open(c / "eventos.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    return evento


# ---------- comandos ----------

def cmd_verificar(_a):
    filas = []

    def ver(nombre, cmd, minimo=None, obligatorio=True):
        try:
            exe = shutil.which(cmd[0]) or cmd[0]  # en Windows resuelve .cmd/.exe (az.cmd, dotnet.exe)
            out = subprocess.run([exe] + cmd[1:], capture_output=True, text=True, timeout=30)
            texto = (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr) else ""
            ok = out.returncode == 0
            if ok and minimo:
                m = re.search(r"(\d+)\.(\d+)", texto)
                ok = bool(m) and (int(m.group(1)), int(m.group(2))) >= minimo
        except (FileNotFoundError, subprocess.TimeoutExpired):
            texto, ok = "no encontrado", False
        filas.append((nombre, ok, texto, obligatorio))

    ver("Python 3.11+", [sys.executable, "--version"], (3, 11))
    ver(".NET SDK 8+", ["dotnet", "--version"], (8, 0))
    ver("Git", ["git", "--version"])
    ver("Terraform 1.9+ (opcional para validar infra)", ["terraform", "version"], (1, 9), obligatorio=False)
    ver("Azure CLI (solo facilitador)", ["az", "version", "--query", "\"azure-cli\"", "--output", "tsv"], obligatorio=False)
    env = (RAIZ / ".env").exists()
    filas.append(("Archivo .env de Jira (opcional)", env, "presente" if env else "sin .env: Jira en modo local", False))
    import urllib.request
    for nombre, url in (("Acceso a PyPI (paquetes de Python)", "https://pypi.org/simple/flask/"), ("Acceso a NuGet (paquetes .NET)", "https://api.nuget.org/v3/index.json")):
        try:
            with urllib.request.urlopen(url, timeout=8) as r:
                filas.append((nombre, r.status == 200, f"HTTP {r.status}", False))
        except Exception as e:  # proxy corporativo, sin red, etc.
            filas.append((nombre, False, f"sin acceso ({type(e).__name__}); corre `preparar` en una red con acceso o configura el proxy", False))
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        filas.append(("Proxy HTTPS", True, "configurado", False))

    print(f"Sistema: {platform.system()} {platform.machine()} · usa `{'python' if os.name == 'nt' else 'python3'}` para los comandos de la fábrica\n")
    falta = False
    for nombre, ok, texto, obligatorio in filas:
        marca = "OK " if ok else ("FALTA" if obligatorio else "--  ")
        falta |= (not ok and obligatorio)
        print(f"[{marca}] {nombre}: {texto}")
    print("\nAmbiente listo." if not falta else "\nFaltan herramientas obligatorias. Revisa README > Preparación.")
    return 1 if falta else 0


def cmd_iniciar(a):
    sol = pathlib.Path(a.solicitud)
    if not sol.is_file():
        sys.exit(f"No existe la solicitud {sol}")
    texto = sol.read_text(encoding="utf-8")
    titulo = re.search(r"^#\s+(.+)$", texto, re.M)
    repo = re.search(r"Repositorio de origen:\s*\**\s*(\S+)", texto)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    cid = f"MIG-{stamp}"
    c = CORRIDAS / cid
    (c / "artefactos").mkdir(parents=True)
    shutil.copy(sol, c / "solicitud.md")
    est = {
        "id": cid,
        "titulo": titulo.group(1).strip() if titulo else sol.stem,
        "solicitud": str(sol),
        "inicio": ahora(),
        "repo_origen": repo.group(1).strip("<>") if repo else None,
        "etapas": {e[0]: {"estado": "pendiente"} for e in ETAPAS},
        "puertas": [],
        "jira": {},
    }
    guardar_estado(c, est)
    CORRIDAS.mkdir(exist_ok=True)
    ACTUAL.write_text(cid)
    registrar(c, {"tipo": "corrida.iniciada", "etapa": "inicio", "agente": "Jefe de fábrica", "resumen": est["titulo"]})

    fuente = RAIZ / "fuente"
    if est["repo_origen"] and not fuente.exists() and not a.sin_clonar:
        print(f"Clonando el origen {est['repo_origen']} en fuente/ ...")
        r = subprocess.run(["git", "clone", "--depth", "1", est["repo_origen"], str(fuente)])
        if r.returncode != 0:
            print("No se pudo clonar el origen. Clónalo a mano en fuente/ y continúa.")
    print(json.dumps({"corrida": cid, "carpeta": str(c.relative_to(RAIZ)), "fuente": str(fuente.relative_to(RAIZ))}, ensure_ascii=False))
    return 0


def cmd_evento(a):
    c = corrida_actual()
    est = leer_estado(c)
    ev = {"tipo": a.tipo, "etapa": a.etapa, "agente": a.agente, "resumen": a.resumen}
    if a.archivo:
        ev["archivo"] = a.archivo
    if a.jira:
        ev["jira"] = a.jira
    if a.tipo in ("etapa.iniciada", "etapa.terminada", "etapa.bloqueada") and a.etapa in est["etapas"]:
        est["etapas"][a.etapa]["estado"] = {"etapa.iniciada": "en_curso", "etapa.terminada": "terminada", "etapa.bloqueada": "bloqueada"}[a.tipo]
        est["etapas"][a.etapa]["actualizado"] = ahora()
        guardar_estado(c, est)
    print(json.dumps(registrar(c, ev), ensure_ascii=False))
    return 0


def cmd_puerta(a):
    """Registra una decisión humana. Si hay hallazgos altos abiertos, exige justificación escrita."""
    c = corrida_actual()
    est = leer_estado(c)
    if a.decision not in ("aprobado", "rechazado", "cambios"):
        sys.exit("decision debe ser: aprobado | rechazado | cambios")
    if not a.por.strip():
        sys.exit("La puerta requiere el nombre de la persona que decide (--por).")
    altos = [h for h in est.get("hallazgos", []) if h.get("severidad") == "alta" and h.get("estado") == "abierto" and h.get("etapa") == a.etapa]
    if a.decision == "aprobado" and altos and len((a.justificacion or "").strip()) < 30:
        sys.exit(f"Hay {len(altos)} hallazgo(s) ALTO(S) abiertos en '{a.etapa}'. Para aprobar se requiere una justificación escrita de al menos 30 caracteres.")
    p = {"etapa": a.etapa, "rol": a.rol, "decision": a.decision, "por": a.por, "justificacion": a.justificacion or "", "ts": ahora(), "hallazgos_altos_abiertos": len(altos)}
    est["puertas"].append(p)
    guardar_estado(c, est)
    registrar(c, {"tipo": "puerta.resuelta", **p, "agente": "Persona"})
    print(json.dumps(p, ensure_ascii=False))
    return 0


def cmd_hallazgo(a):
    c = corrida_actual()
    est = leer_estado(c)
    est.setdefault("hallazgos", [])
    hid = f"H{len(est['hallazgos']) + 1:02d}"
    h = {"id": hid, "etapa": a.etapa, "severidad": a.severidad, "titulo": a.titulo, "detalle": a.detalle or "", "estado": "abierto", "ts": ahora()}
    est["hallazgos"].append(h)
    guardar_estado(c, est)
    registrar(c, {"tipo": "hallazgo", "etapa": a.etapa, "agente": a.agente, "resumen": f"[{a.severidad}] {a.titulo}", "hallazgo": hid})
    print(json.dumps(h, ensure_ascii=False))
    return 0


def cmd_cerrar_hallazgo(a):
    c = corrida_actual()
    est = leer_estado(c)
    for h in est.get("hallazgos", []):
        if h["id"] == a.id:
            h["estado"] = a.estado
            h["resolucion"] = a.resolucion
            guardar_estado(c, est)
            registrar(c, {"tipo": "hallazgo.cerrado", "etapa": h["etapa"], "agente": "Persona", "resumen": f"{a.id}: {a.estado} · {a.resolucion}"})
            print(json.dumps(h, ensure_ascii=False))
            return 0
    sys.exit(f"No existe el hallazgo {a.id}")


def cmd_estado(_a):
    c = corrida_actual()
    est = leer_estado(c)
    print(f"Corrida {est['id']} · {est['titulo']}\n")
    for clave, nombre, agente, rol in ETAPAS:
        e = est["etapas"][clave]["estado"]
        puertas = [p for p in est["puertas"] if p["etapa"] == clave]
        pu = f" · puerta: {puertas[-1]['decision']} por {puertas[-1]['por']}" if puertas else (f" · puerta pendiente ({rol})" if rol else "")
        print(f"  {e:<10} {nombre} ({agente}){pu}")
    abiertos = [h for h in est.get("hallazgos", []) if h["estado"] == "abierto"]
    if abiertos:
        print("\nHallazgos abiertos:")
        for h in abiertos:
            print(f"  {h['id']} [{h['severidad']}] {h['titulo']} ({h['etapa']})")
    if est.get("jira"):
        print(f"\nJira: {json.dumps(est['jira'], ensure_ascii=False)[:300]}")
    return 0


def cmd_costo(a):
    c = pathlib.Path(a.corrida) if a.corrida else corrida_actual()
    costo.imprimir(costo.calcular(c, a.raiz or RAIZ, ETAPAS))
    return 0


def cmd_replay(_a):
    sys.path.insert(0, str(RAIZ / ".github" / "skills" / "replay" / "scripts"))
    import replay  # noqa: E402
    c = corrida_actual()
    try:
        costo.calcular(c, RAIZ, ETAPAS)
    except Exception as e:  # el replay no depende del costo
        print(f"(No se pudo calcular el costo: {e})")
    salida = replay.generar(c, ETAPAS)
    print(f"Replay generado: {salida.relative_to(RAIZ)}")
    return 0


def cmd_archivar(_a):
    """Mueve la corrida activa, fuente/ y destino/ a corridas/archivo/<id>/ (no borra nada) para empezar de cero."""
    for cual in ("origen", "destino"):
        servicios.detener(cual)
    cid = ACTUAL.read_text().strip() if ACTUAL.exists() else dt.datetime.now().strftime("sin-corrida-%Y%m%d-%H%M%S")
    archivo = CORRIDAS / "archivo" / cid
    archivo.mkdir(parents=True, exist_ok=True)
    movidos = []
    if (CORRIDAS / cid).is_dir():
        shutil.move(str(CORRIDAS / cid), str(archivo / "corrida")); movidos.append(f"corridas/{cid}")
    for carpeta in ("fuente", "destino", ".venv-fuente"):
        if (RAIZ / carpeta).exists():
            shutil.move(str(RAIZ / carpeta), str(archivo / carpeta)); movidos.append(carpeta)
    if ACTUAL.exists():
        ACTUAL.unlink()
    print(json.dumps({"archivado_en": str(archivo.relative_to(RAIZ)), "movidos": movidos}, ensure_ascii=False))
    return 0


def cmd_servicio(a):
    if a.cmd == "preparar":
        servicios.preparar_origen()
        servicios.preparar_destino()
        print("Dependencias listas: origen (.venv-fuente) y paquetes NuGet de la plantilla.")
        return 0
    if a.cmd == "medir":
        return servicios.medir(a.base, a.ruta, a.n, a.concurrentes)
    if a.cmd == "destino" and a.accion == "crear":
        if not a.nombre:
            sys.exit("Indica --nombre, por ejemplo --nombre Transferencias")
        return servicios.crear_destino(a.nombre) or 0
    if a.accion == "iniciar":
        return servicios.iniciar(a.cmd, a.puerto)
    if a.accion == "detener":
        return servicios.detener(a.cmd)
    return servicios.estado_servicio(a.cmd)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("verificar").set_defaults(f=cmd_verificar)
    s.add_parser("preparar").set_defaults(f=cmd_servicio)
    s.add_parser("archivar").set_defaults(f=cmd_archivar)
    o = s.add_parser("origen"); o.add_argument("accion", choices=["iniciar", "salud", "detener"]); o.add_argument("--puerto", type=int); o.set_defaults(f=cmd_servicio)
    d = s.add_parser("destino"); d.add_argument("accion", choices=["crear", "iniciar", "salud", "detener"]); d.add_argument("--puerto", type=int)
    d.add_argument("--nombre"); d.set_defaults(f=cmd_servicio)
    m = s.add_parser("medir"); m.add_argument("--base", required=True); m.add_argument("--ruta", default="/api/salud")
    m.add_argument("--n", type=int, default=50); m.add_argument("--concurrentes", type=int, default=5); m.set_defaults(f=cmd_servicio)
    i = s.add_parser("iniciar"); i.add_argument("solicitud"); i.add_argument("--sin-clonar", action="store_true"); i.set_defaults(f=cmd_iniciar)
    e = s.add_parser("evento")
    for k in ("--etapa", "--agente", "--tipo", "--resumen"):
        e.add_argument(k, required=True)
    e.add_argument("--archivo"); e.add_argument("--jira"); e.set_defaults(f=cmd_evento)
    g = s.add_parser("puerta")
    for k in ("--etapa", "--rol", "--decision", "--por"):
        g.add_argument(k, required=True)
    g.add_argument("--justificacion", default=""); g.set_defaults(f=cmd_puerta)
    h = s.add_parser("hallazgo")
    for k in ("--etapa", "--agente", "--severidad", "--titulo"):
        h.add_argument(k, required=True)
    h.add_argument("--detalle"); h.set_defaults(f=cmd_hallazgo)
    ch = s.add_parser("cerrar-hallazgo"); ch.add_argument("id"); ch.add_argument("--estado", choices=["corregido", "aceptado", "descartado"], required=True)
    ch.add_argument("--resolucion", required=True); ch.set_defaults(f=cmd_cerrar_hallazgo)
    s.add_parser("estado").set_defaults(f=cmd_estado)
    s.add_parser("replay").set_defaults(f=cmd_replay)
    co = s.add_parser("costo"); co.add_argument("--corrida"); co.add_argument("--raiz", help=argparse.SUPPRESS); co.set_defaults(f=cmd_costo)
    a = p.parse_args()
    sys.exit(a.f(a))


if __name__ == "__main__":
    main()
