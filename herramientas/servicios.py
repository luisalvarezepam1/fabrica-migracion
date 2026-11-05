"""Levantar, revisar y detener el origen y el destino, igual en Windows, macOS y Linux (solo Python estándar).

Lo usan los agentes a través de fabrica.py para no depender de comandos de una terminal en particular
(`&`, `curl`, `lsof`, variables de entorno en línea...).
"""
import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ESTADO = RAIZ / "corridas" / ".servicios"
ES_WINDOWS = os.name == "nt"
PUERTOS = {"origen": 5050, "destino": 5080}  # en macOS el 5000 lo ocupa AirPlay Receiver


def python_venv(venv):
    return venv / ("Scripts/python.exe" if ES_WINDOWS else "bin/python")


def preparar_origen():
    """Crea .venv-fuente e instala las dependencias del origen (fuente/requirements.txt)."""
    fuente = RAIZ / "fuente"
    if not (fuente / "requirements.txt").exists():
        sys.exit("No existe fuente/requirements.txt. Inicia primero la corrida (fabrica.py iniciar ...).")
    venv = RAIZ / ".venv-fuente"
    if not python_venv(venv).exists():
        print("Creando .venv-fuente ...")
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    print("Instalando dependencias del origen ...")
    subprocess.run([str(python_venv(venv)), "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", str(fuente / "requirements.txt")], check=True)
    return python_venv(venv)


def preparar_destino():
    """Descarga los paquetes NuGet de la plantilla aprobada (para que la migración no espere descargas)."""
    plantilla = RAIZ / "plataforma" / "plantillas" / "dotnet-api"
    print("Restaurando paquetes de la plantilla .NET ...")
    subprocess.run(["dotnet", "restore", str(plantilla / "Plantilla.sln")], check=True)


def crear_destino(nombre):
    """Copia la plantilla aprobada a destino/ y la renombra (Plantilla -> <nombre>)."""
    destino = RAIZ / "destino"
    if destino.exists() and any(destino.iterdir()):
        sys.exit("destino/ ya existe y no está vacío. No se sobrescribe.")
    plantilla = RAIZ / "plataforma" / "plantillas" / "dotnet-api"
    shutil.copytree(plantilla, destino, ignore=shutil.ignore_patterns("bin", "obj"), dirs_exist_ok=True)
    for ruta in sorted(destino.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if ruta.is_file() and ruta.suffix in {".cs", ".csproj", ".sln", ".json", ".html", ".md"}:
            texto = ruta.read_text(encoding="utf-8")
            if "Plantilla" in texto:
                ruta.write_text(texto.replace("Plantilla", nombre), encoding="utf-8")
        if "Plantilla" in ruta.name:
            ruta.rename(ruta.with_name(ruta.name.replace("Plantilla", nombre)))
    print(json.dumps({"destino": "destino/", "solucion": f"destino/{nombre}.sln", "api": f"destino/src/{nombre}.Api", "pruebas": f"destino/tests/{nombre}.Tests"}, ensure_ascii=False))


def _estado():
    return json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}


def _guardar(est):
    ESTADO.parent.mkdir(exist_ok=True)
    ESTADO.write_text(json.dumps(est, indent=2), encoding="utf-8")


def salud(url, intentos=1, espera=1.0):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(url.rstrip("/") + "/api/salud", timeout=5) as r:
                cuerpo = json.loads(r.read().decode("utf-8"))
                if cuerpo.get("estado") == "ok":
                    return cuerpo
        except (urllib.error.URLError, OSError, ValueError):
            pass
        if i < intentos - 1:
            time.sleep(espera)
    return None


def _puerto_ocupado(puerto):
    import socket
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", puerto)) == 0


def iniciar(cual, puerto=None):
    puerto = puerto or PUERTOS[cual]
    url = f"http://127.0.0.1:{puerto}"
    est = _estado()
    if cual in est and salud(est[cual]["url"]):
        print(json.dumps({"servicio": cual, "url": est[cual]["url"], "estado": "ya estaba corriendo"}, ensure_ascii=False))
        return 0
    if _puerto_ocupado(puerto):
        sys.exit(f"El puerto {puerto} está ocupado por otro programa. Usa --puerto con otro valor.")
    bd = pathlib.Path(tempfile.gettempdir()) / f"fabrica-{cual}-{int(time.time())}.db"
    env = dict(os.environ, DATABASE_PATH=str(bd), DEMO_MODE="1", PORT=str(puerto), PYTHONUNBUFFERED="1")
    logs = RAIZ / "corridas" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    log = open(logs / f"{cual}.log", "w", encoding="utf-8")
    if cual == "origen":
        py = preparar_origen() if not python_venv(RAIZ / ".venv-fuente").exists() else python_venv(RAIZ / ".venv-fuente")
        cmd = [str(py), "-c", f"from wsgi import app; app.run(host='127.0.0.1', port={puerto})"]
        cwd = RAIZ / "fuente"
    else:
        proyectos = sorted((RAIZ / "destino" / "src").glob("*.Api/*.csproj"))
        if not proyectos:
            sys.exit("No encuentro destino/src/*.Api/*.csproj. Crea el destino con: fabrica.py destino crear --nombre <Nombre>")
        cmd = ["dotnet", "run", "--project", str(proyectos[0]), "--urls", url]
        cwd = RAIZ
    extra = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS} if ES_WINDOWS else {"start_new_session": True}
    p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **extra)
    est[cual] = {"pid": p.pid, "url": url, "bd": str(bd), "log": str((logs / f"{cual}.log").relative_to(RAIZ))}
    _guardar(est)
    s = salud(url, intentos=90 if cual == "destino" else 30, espera=1.0)
    if not s:
        detener(cual)
        sys.exit(f"{cual} no respondió en {url}/api/salud. Revisa {est[cual]['log']}.")
    print(json.dumps({"servicio": cual, "url": url, "version": s.get("version"), "log": est[cual]["log"]}, ensure_ascii=False))
    return 0


def detener(cual):
    est = _estado()
    info = est.pop(cual, None)
    if not info:
        print(f"{cual} no estaba corriendo.")
        return 0
    try:
        if ES_WINDOWS:
            subprocess.run(["taskkill", "/PID", str(info["pid"]), "/T", "/F"], capture_output=True)
        else:
            os.killpg(info["pid"], signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        pass
    _guardar(est)
    print(f"{cual} detenido.")
    return 0


def estado_servicio(cual):
    info = _estado().get(cual)
    if not info:
        print(f"{cual}: detenido")
        return 1
    s = salud(info["url"])
    print(f"{cual}: {'corriendo' if s else 'no responde'} en {info['url']}")
    return 0 if s else 1


def medir(base, ruta, n=50, concurrentes=5):
    """p95 sencillo: n llamadas secuenciales y luego n llamadas en grupos concurrentes."""
    import concurrent.futures as cf

    def una():
        t = time.perf_counter()
        with urllib.request.urlopen(base.rstrip("/") + ruta, timeout=10) as r:
            r.read()
        return (time.perf_counter() - t) * 1000

    def p95(v):
        v = sorted(v)
        return round(v[max(0, int(len(v) * 0.95) - 1)], 1)

    sec = [una() for _ in range(n)]
    with cf.ThreadPoolExecutor(max_workers=concurrentes) as ex:
        con = list(ex.map(lambda _: una(), range(n)))
    print(json.dumps({"ruta": ruta, "llamadas": n, "p95_secuencial_ms": p95(sec), "p95_concurrente_ms": p95(con), "concurrentes": concurrentes}, ensure_ascii=False))
    return 0
