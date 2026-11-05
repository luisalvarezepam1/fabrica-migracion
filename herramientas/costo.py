"""Costo de una corrida: tokens y créditos de Copilot por agente y por etapa.

Lee el historial de chat que VS Code guarda en disco para esta carpeta (workspaceStorage/*/chatSessions)
y suma las solicitudes hechas desde el inicio de la corrida. No envía nada a ningún lado.

El precio por crédito se configura con FABRICA_USD_POR_CREDITO (por defecto 0.01, el valor de
1 GitHub AI Credit). Compara siempre contra tu facturación real en GitHub (Settings › Billing › Usage).
"""
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.parse


def _carpetas_storage():
    casa = pathlib.Path.home()
    bases = []
    if sys.platform == "darwin":
        bases += [casa / "Library/Application Support" / n for n in ("Code", "Code - Insiders")]
    elif os.name == "nt":
        appdata = pathlib.Path(os.environ.get("APPDATA", casa / "AppData/Roaming"))
        bases += [appdata / n for n in ("Code", "Code - Insiders")]
    else:
        bases += [casa / ".config" / n for n in ("Code", "Code - Insiders")]
    bases += [casa / ".vscode-remote/data", casa / ".vscode-server/data"]  # Codespaces / remoto
    return [b / "User/workspaceStorage" for b in bases if (b / "User/workspaceStorage").is_dir()]


def _sesiones_de(raiz):
    raiz = pathlib.Path(raiz).resolve()
    for base in _carpetas_storage():
        for ws in base.glob("*/workspace.json"):
            try:
                carpeta = json.loads(ws.read_text(encoding="utf-8")).get("folder", "")
            except (OSError, ValueError):
                continue
            ruta = urllib.parse.unquote(urllib.parse.urlparse(carpeta).path)
            if os.name == "nt" and ruta.startswith("/"):
                ruta = ruta[1:]
            try:
                if pathlib.Path(ruta).resolve() == raiz:
                    yield from (ws.parent / "chatSessions").glob("*.json*")
            except OSError:
                continue


def _cargar(archivo):
    """Reconstruye la sesión: .json completo o .jsonl con parches (kind 0 = base, 1 = asignar, 2 = agregar)."""
    texto = archivo.read_text(encoding="utf-8")
    if archivo.suffix == ".json":
        return json.loads(texto)
    raiz = None
    for linea in texto.splitlines():
        if not linea.strip():
            continue
        o = json.loads(linea)
        if o["kind"] == 0:
            raiz = o["v"]
            continue
        k, t = o["k"], raiz
        try:
            for p in (k[:-1] if o["kind"] == 1 else k):
                t = t[p]
            if o["kind"] == 1:
                t[k[-1]] = o["v"]
            elif "i" in o:
                t[o["i"]:] = o["v"]
            else:
                t.extend(o["v"])
        except (KeyError, IndexError, TypeError):
            continue
    return raiz or {}


def _agente(req):
    ruta = (((req.get("modeInfo") or {}).get("modeInstructions") or {}).get("uri") or {}).get("path", "")
    nombre = pathlib.Path(ruta).name
    return nombre.replace(".agent.md", "").capitalize() if nombre.endswith(".agent.md") else "Agent"


def _modelo(req):
    texto = json.dumps(req.get("result") or {}) + json.dumps(req.get("response") or [])
    i = texto.find('"modelName"')
    if i >= 0:
        resto = texto[i + 11:].split('"')
        return resto[1] if len(resto) > 1 else req.get("modelId")
    return req.get("modelId")


def calcular(corrida, raiz, etapas):
    est = json.loads((corrida / "estado.json").read_text(encoding="utf-8"))
    eventos = [json.loads(l) for l in (corrida / "eventos.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    desde = dt.datetime.fromisoformat(est["inicio"]).timestamp() * 1000 - 10 * 60 * 1000  # incluye la solicitud que inició la corrida
    hasta = dt.datetime.fromisoformat(eventos[-1]["ts"]).timestamp() * 1000 + 15 * 60 * 1000 if est["etapas"]["aprendizaje"]["estado"] == "terminada" else float("inf")
    etapa_de = {ag.lower(): clave for clave, _, ag, _ in etapas}
    etapa_de["fabrica"] = "inicio"
    usd = float(os.environ.get("FABRICA_USD_POR_CREDITO", "0.01"))
    por_agente, modelos, total = {}, {}, {"solicitudes": 0, "tokens_entrada": 0, "tokens_salida": 0, "creditos": 0.0}
    for archivo in _sesiones_de(raiz):
        try:
            sesion = _cargar(archivo)
        except (OSError, ValueError):
            continue
        for req in sesion.get("requests", []):
            ts = req.get("timestamp") or 0
            if not (desde <= ts <= hasta):
                continue
            ag = _agente(req)
            fila = por_agente.setdefault(ag, {"etapa": etapa_de.get(ag.lower(), "otra"), "solicitudes": 0, "tokens_entrada": 0, "tokens_salida": 0, "creditos": 0.0})
            for destino in (fila, total):
                destino["solicitudes"] += 1
                destino["tokens_entrada"] += int(req.get("promptTokens") or 0)
                destino["tokens_salida"] += int(req.get("completionTokens") or 0)
                destino["creditos"] += float(req.get("copilotCredits") or 0)
            m = _modelo(req) or "desconocido"
            modelos[m] = modelos.get(m, 0) + 1
    previo = corrida / "costo.json"
    if total["solicitudes"] == 0 and previo.exists():
        return json.loads(previo.read_text(encoding="utf-8"))  # sin historial en esta máquina: conserva el cálculo anterior
    for d in list(por_agente.values()) + [total]:
        d["creditos"] = round(d["creditos"], 2)
        d["usd_estimado"] = round(d["creditos"] * usd, 4)
    resultado = {"corrida": est["id"], "usd_por_credito": usd, "total": total, "por_agente": por_agente, "modelos": modelos,
                 "nota": "Estimación a partir del historial local de VS Code. Compárala con GitHub › Settings › Billing › Usage."}
    (corrida / "costo.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return resultado


def imprimir(r):
    t = r["total"]
    print(f"Corrida {r['corrida']} · {t['solicitudes']} solicitudes · {t['tokens_entrada']:,} tokens de entrada · {t['tokens_salida']:,} de salida")
    print(f"Créditos: {t['creditos']} · costo estimado USD {t['usd_estimado']} (a USD {r['usd_por_credito']} por crédito)\n")
    print(f"{'Agente':<15}{'Etapa':<17}{'Solic.':>7}{'Entrada':>12}{'Salida':>10}{'Créditos':>10}{'USD':>9}")
    for ag, d in sorted(r["por_agente"].items(), key=lambda x: -x[1]["creditos"]):
        print(f"{ag:<15}{d['etapa']:<17}{d['solicitudes']:>7}{d['tokens_entrada']:>12,}{d['tokens_salida']:>10,}{d['creditos']:>10}{d['usd_estimado']:>9}")
    print("\nModelos: " + ", ".join(f"{m} ({n})" for m, n in r["modelos"].items()))
    print(r["nota"])
