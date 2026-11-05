#!/usr/bin/env python3
"""Tareas de la migración en Jira Cloud (REST v3), sin dependencias.

Lee la conexión de .env en la raíz de la fábrica (nunca imprime el token):
  JIRA_URL=https://<tu-sitio>.atlassian.net
  JIRA_EMAIL=persona@empresa.com
  JIRA_TOKEN=<token de API de Atlassian>
  JIRA_PROYECTO=MIG
  JIRA_TIPO_EPICA=Epic         (opcional; p. ej. "Épica" si tu Jira está en español)
  JIRA_TIPO_TAREA=Task         (opcional; p. ej. "Tarea")

Sin .env (o con JIRA_MODO=local) trabaja en modo local: genera claves LOCAL-n y un tablero en Markdown.

  python3 jira.py probar
  python3 jira.py tipos
  python3 jira.py crear-plan corridas/<id>/artefactos/plan-jira.json
  python3 jira.py mover <CLAVE|ref> "En curso"
  python3 jira.py comentar <CLAVE|ref> "texto"
"""
import base64
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parents[4]
CORRIDAS = RAIZ / "corridas"


def cargar_env():
    env = {}
    f = RAIZ / ".env"
    if f.exists():
        for linea in f.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("JIRA_URL", "JIRA_EMAIL", "JIRA_TOKEN", "JIRA_PROYECTO", "JIRA_MODO", "JIRA_TIPO_EPICA", "JIRA_TIPO_TAREA"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


ENV = cargar_env()

# Los agentes usan los estados en español; Jira puede tenerlos en inglés o con otros nombres.
ALIAS_ESTADOS = {
    "por hacer": ["to do", "selected for development", "backlog", "tareas por hacer"],
    "en curso": ["in progress", "en progreso"],
    "en revisión": ["in review", "en revision", "review"],
    "listo": ["done", "finalizado", "hecho", "listo"],
}
LOCAL = ENV.get("JIRA_MODO") == "local" or not all(ENV.get(k) for k in ("JIRA_URL", "JIRA_EMAIL", "JIRA_TOKEN", "JIRA_PROYECTO"))


def corrida():
    actual = CORRIDAS / ".actual"
    if not actual.exists():
        sys.exit("No hay corrida activa (python3 herramientas/fabrica.py iniciar ...).")
    return CORRIDAS / actual.read_text().strip()


def api(metodo, ruta, cuerpo=None):
    url = ENV["JIRA_URL"].rstrip("/") + ruta
    cred = base64.b64encode(f"{ENV['JIRA_EMAIL']}:{ENV['JIRA_TOKEN']}".encode()).decode()
    req = urllib.request.Request(url, method=metodo, data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
                                 headers={"Authorization": f"Basic {cred}", "Accept": "application/json", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            t = r.read().decode()
            return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        detalle = e.read().decode()[:600]
        sys.exit(f"Jira respondió {e.code} en {metodo} {ruta}: {detalle}")


def adf(texto):
    """Texto plano (con saltos de línea y viñetas '- ') -> Atlassian Document Format."""
    bloques, lista = [], None
    for linea in (texto or "").splitlines():
        if linea.startswith("- "):
            lista = lista or {"type": "bulletList", "content": []}
            lista["content"].append({"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": linea[2:]}]}]})
            continue
        if lista:
            bloques.append(lista); lista = None
        if linea.strip():
            bloques.append({"type": "paragraph", "content": [{"type": "text", "text": linea}]})
    if lista:
        bloques.append(lista)
    return {"type": "doc", "version": 1, "content": bloques or [{"type": "paragraph", "content": []}]}


def guardar_mapa(c, mapa):
    (c / "jira.json").write_text(json.dumps(mapa, ensure_ascii=False, indent=2), encoding="utf-8")
    est = json.loads((c / "estado.json").read_text(encoding="utf-8"))
    est["jira"] = {"modo": mapa["modo"], "proyecto": mapa.get("proyecto"), "epica": mapa.get("epica"), "url": mapa.get("url"),
                   "tareas": {r: v["clave"] for r, v in mapa["tareas"].items()}}
    (c / "estado.json").write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")


def leer_mapa(c):
    f = c / "jira.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def tablero_local(c, mapa):
    filas = ["# Tablero local de la migración", "", f"Épica **{mapa['epica']}** · {mapa['epica_resumen']}", "",
             "| Clave | Ref | Etapa | Estado | Resumen |", "|---|---|---|---|---|"]
    for ref, t in mapa["tareas"].items():
        filas.append(f"| {t['clave']} | {ref} | {t.get('etapa', '')} | {t.get('estado', 'Por hacer')} | {t['resumen']} |")
    (c / "artefactos" / "tablero-jira.md").write_text("\n".join(filas) + "\n", encoding="utf-8")


def cmd_probar():
    if LOCAL:
        print("Modo local: no hay conexión a Jira configurada en .env. Las tareas se guardarán en la corrida.")
        return
    yo = api("GET", "/rest/api/3/myself")
    pr = api("GET", f"/rest/api/3/project/{ENV['JIRA_PROYECTO']}")
    print(f"Conectado a {ENV['JIRA_URL']} como {yo.get('displayName')} · proyecto {pr.get('key')} ({pr.get('name')})")


def cmd_tipos():
    if LOCAL:
        print("Modo local: tipos Epic y Task.")
        return
    pr = api("GET", f"/rest/api/3/project/{ENV['JIRA_PROYECTO']}")
    for t in pr.get("issueTypes", []):
        print(f"- {t['name']}{' (subtarea)' if t.get('subtask') else ''}")


def cmd_crear_plan(archivo):
    c = corrida()
    plan = json.loads(pathlib.Path(archivo).read_text(encoding="utf-8"))
    if leer_mapa(c):
        sys.exit("Esta corrida ya tiene tareas en Jira (jira.json). No se crean duplicados.")
    est = json.loads((c / "estado.json").read_text(encoding="utf-8"))
    etiquetas = ["fabrica-migracion", est["id"].lower()]
    mapa = {"modo": "local" if LOCAL else "jira", "tareas": {}}
    if LOCAL:
        mapa.update(proyecto="LOCAL", epica="LOCAL-1", epica_resumen=plan["epica"]["resumen"])
        for n, it in enumerate(plan["tareas"], start=2):
            mapa["tareas"][it["ref"]] = {"clave": f"LOCAL-{n}", "resumen": it["resumen"], "etapa": it.get("etapa"), "estado": "Por hacer"}
        guardar_mapa(c, mapa)
        tablero_local(c, mapa)
        print(f"Modo local: épica LOCAL-1 y {len(plan['tareas'])} tareas -> {c.relative_to(RAIZ)}/artefactos/tablero-jira.md")
        return
    proyecto = ENV["JIRA_PROYECTO"]
    t_epica, t_tarea = ENV.get("JIRA_TIPO_EPICA", "Epic"), ENV.get("JIRA_TIPO_TAREA", "Task")
    ep = api("POST", "/rest/api/3/issue", {"fields": {"project": {"key": proyecto}, "issuetype": {"name": t_epica}, "summary": plan["epica"]["resumen"],
                                                      "description": adf(plan["epica"].get("descripcion", "")), "labels": etiquetas}})
    mapa.update(proyecto=proyecto, epica=ep["key"], epica_resumen=plan["epica"]["resumen"], url=f"{ENV['JIRA_URL'].rstrip('/')}/browse/{ep['key']}")
    for it in plan["tareas"]:
        campos = {"project": {"key": proyecto}, "issuetype": {"name": it.get("tipo", t_tarea)}, "summary": it["resumen"],
                  "description": adf(it.get("descripcion", "")), "labels": etiquetas + ([f"etapa-{it['etapa']}"] if it.get("etapa") else []), "parent": {"key": ep["key"]}}
        r = api("POST", "/rest/api/3/issue", {"fields": campos})
        mapa["tareas"][it["ref"]] = {"clave": r["key"], "resumen": it["resumen"], "etapa": it.get("etapa"), "estado": "Por hacer"}
        guardar_mapa(c, mapa)
    print(f"Jira: épica {ep['key']} y {len(plan['tareas'])} tareas creadas · {mapa['url']}")


def resolver(c, clave):
    mapa = leer_mapa(c)
    if not mapa:
        sys.exit("La corrida no tiene plan en Jira todavía.")
    if clave in mapa["tareas"]:
        return mapa, clave, mapa["tareas"][clave]["clave"]
    for ref, t in mapa["tareas"].items():
        if t["clave"] == clave:
            return mapa, ref, clave
    if clave == mapa.get("epica"):
        return mapa, None, clave
    sys.exit(f"No encuentro {clave} en el plan de esta corrida.")


def cmd_mover(clave, estado):
    c = corrida()
    mapa, ref, key = resolver(c, clave)
    if not LOCAL and mapa["modo"] == "jira":
        trs = api("GET", f"/rest/api/3/issue/{key}/transitions")["transitions"]
        candidatos = [estado.lower()] + ALIAS_ESTADOS.get(estado.lower(), [])
        objetivo = next((t for c in candidatos for t in trs if t["name"].lower() == c or t["to"]["name"].lower() == c), None)
        if not objetivo:
            sys.exit(f"Transiciones disponibles para {key}: {', '.join(t['name'] + ' -> ' + t['to']['name'] for t in trs)}")
        api("POST", f"/rest/api/3/issue/{key}/transitions", {"transition": {"id": objetivo["id"]}})
    if ref:
        mapa["tareas"][ref]["estado"] = estado
        guardar_mapa(c, mapa)
        if mapa["modo"] == "local":
            tablero_local(c, mapa)
    print(f"{key} -> {estado}")


def cmd_comentar(clave, texto):
    c = corrida()
    mapa, ref, key = resolver(c, clave)
    if not LOCAL and mapa["modo"] == "jira":
        api("POST", f"/rest/api/3/issue/{key}/comment", {"body": adf(texto)})
    else:
        with open(c / "artefactos" / "comentarios-jira.md", "a", encoding="utf-8") as f:
            f.write(f"- **{key}**: {texto}\n")
    print(f"Comentario agregado a {key}")


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return
    cmd = a[0]
    if cmd == "probar":
        cmd_probar()
    elif cmd == "tipos":
        cmd_tipos()
    elif cmd == "crear-plan" and len(a) == 2:
        cmd_crear_plan(a[1])
    elif cmd == "mover" and len(a) == 3:
        cmd_mover(a[1], a[2])
    elif cmd == "comentar" and len(a) == 3:
        cmd_comentar(a[1], a[2])
    else:
        print(__doc__); sys.exit(2)


if __name__ == "__main__":
    main()
