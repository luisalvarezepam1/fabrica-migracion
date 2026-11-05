#!/usr/bin/env python3
"""Pruebas de contrato de caja negra (HTTP), sin dependencias.

  capturar  Corre los casos contra el ORIGEN y guarda las respuestas como referencia (golden master).
  comparar  Corre los mismos casos contra el DESTINO y compara con la referencia.

  python3 contrato.py capturar --base http://127.0.0.1:5000 --casos casos.json --salida referencia.json
  python3 contrato.py comparar --base http://127.0.0.1:5080 --casos casos.json --referencia referencia.json --reporte reporte.md

Formato de casos.json:
{
  "ignorar": ["fecha", "fecha_reverso", "ahora"],          # campos volátiles (en cualquier nivel)
  "cabeceras": ["Idempotent-Replay"],                       # cabeceras de respuesta que también se comparan
  "casos": [
    {"id": "C01", "titulo": "...", "regla": "R-01", "pasos": [
      {"reiniciar": true},
      {"metodo": "POST", "ruta": "/api/transferencias", "cabeceras": {"X-Demo-Ahora": "2026-11-05T10:00:00-04:00"},
       "cuerpo": {...}, "guardar": {"tid": "id"}},
      {"metodo": "GET", "ruta": "/api/transferencias/{tid}"},
      {"metodo": "GET", "ruta": "/api/cuentas/7001-0001", "esperado": {"estado": 200, "cuerpo": {...}}}   # opcional: decisión humana
    ]}
  ]
}
"esperado" en un paso reemplaza la referencia del origen: se usa cuando una persona decidió que el destino
debe comportarse distinto (por ejemplo, corregir un defecto heredado).
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request

RESET = "/api/demo/reiniciar"


def pedir(base, metodo, ruta, cabeceras=None, cuerpo=None):
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    h = {"Accept": "application/json", **(cabeceras or {})}
    if datos is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(base.rstrip("/") + ruta, data=datos, method=metodo, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            estado, cab, texto = r.status, dict(r.headers), r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        estado, cab, texto = e.code, dict(e.headers), e.read().decode("utf-8")
    try:
        cuerpo_r = json.loads(texto) if texto else None
    except json.JSONDecodeError:
        cuerpo_r = {"_texto": texto[:500]}
    return estado, cab, cuerpo_r


def normalizar(v, ignorar):
    if isinstance(v, dict):
        return {k: ("<volátil>" if k in ignorar and v[k] is not None else normalizar(x, ignorar)) for k, x in v.items()}
    if isinstance(v, list):
        return [normalizar(x, ignorar) for x in v]
    return v


def sustituir(texto, vars_):
    return re.sub(r"\{(\w+)\}", lambda m: str(vars_.get(m.group(1), m.group(0))), texto)


def extraer(cuerpo, ruta):
    v = cuerpo
    for parte in ruta.split("."):
        v = v[int(parte)] if isinstance(v, list) else (v or {}).get(parte)
    return v


def correr(base, spec):
    ignorar = set(spec.get("ignorar", []))
    cab_comp = [c.lower() for c in spec.get("cabeceras", [])]
    salida = {}
    for caso in spec["casos"]:
        vars_, pasos = {}, []
        for p in caso["pasos"]:
            if p.get("reiniciar"):
                est, _, _ = pedir(base, "POST", RESET)
                pasos.append({"reiniciar": True, "estado": est})
                continue
            ruta = sustituir(p["ruta"], vars_)
            cuerpo = json.loads(sustituir(json.dumps(p["cuerpo"]), vars_)) if "cuerpo" in p else None
            est, cab, cuerpo_r = pedir(base, p.get("metodo", "GET"), ruta, p.get("cabeceras"), cuerpo)
            for nombre, campo in (p.get("guardar") or {}).items():
                try:
                    vars_[nombre] = extraer(cuerpo_r, campo)
                except (KeyError, IndexError, TypeError, ValueError):
                    vars_[nombre] = None
            cab_n = {k.lower(): v for k, v in cab.items() if k.lower() in cab_comp}
            pasos.append({"metodo": p.get("metodo", "GET"), "ruta": ruta, "estado": est, "cabeceras": cab_n, "cuerpo": normalizar(cuerpo_r, ignorar)})
        salida[caso["id"]] = pasos
    return salida


def diferencias(a, b, ruta="$"):
    if type(a) is not type(b):
        return [f"{ruta}: esperado {json.dumps(a, ensure_ascii=False)} · obtenido {json.dumps(b, ensure_ascii=False)}"]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in b:
                out.append(f"{ruta}.{k}: falta en el destino")
            elif k not in a:
                out.append(f"{ruta}.{k}: sobra en el destino")
            else:
                out += diferencias(a[k], b[k], f"{ruta}.{k}")
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [f"{ruta}: {len(a)} elementos esperados · {len(b)} obtenidos"] + sum((diferencias(x, y, f"{ruta}[{i}]") for i, (x, y) in enumerate(zip(a, b))), [])
        return sum((diferencias(x, y, f"{ruta}[{i}]") for i, (x, y) in enumerate(zip(a, b))), [])
    return [] if a == b else [f"{ruta}: esperado {json.dumps(a, ensure_ascii=False)} · obtenido {json.dumps(b, ensure_ascii=False)}"]


def cmd_capturar(a):
    spec = json.load(open(a.casos, encoding="utf-8"))
    ref = {"base": a.base, "resultados": correr(a.base, spec)}
    json.dump(ref, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    n = sum(len(v) for v in ref["resultados"].values())
    print(f"Referencia capturada: {len(ref['resultados'])} casos, {n} pasos -> {a.salida}")
    return 0


def cmd_comparar(a):
    spec = json.load(open(a.casos, encoding="utf-8"))
    ref = json.load(open(a.referencia, encoding="utf-8"))["resultados"]
    obt = correr(a.base, spec)
    filas, total_ok = [], 0
    for caso in spec["casos"]:
        cid = caso["id"]
        difs = []
        for i, (pr, po) in enumerate(zip(ref.get(cid, []), obt.get(cid, []))):
            esperado = caso["pasos"][i].get("esperado")
            if esperado is not None:
                pr = {**pr, "estado": esperado.get("estado", pr.get("estado")), "cuerpo": esperado.get("cuerpo", pr.get("cuerpo"))}
            for k in ("estado", "cabeceras", "cuerpo"):
                if k in pr:
                    difs += [f"paso {i + 1} {po.get('metodo', '')} {po.get('ruta', '')} · {d}" for d in diferencias(pr.get(k), po.get(k), k)]
        if len(ref.get(cid, [])) != len(obt.get(cid, [])):
            difs.append("distinto número de pasos")
        total_ok += not difs
        filas.append((caso, difs))
    lineas = [f"# Reporte de equivalencia", "", f"Destino: `{a.base}` · Casos: {len(filas)} · Iguales: {total_ok} · Distintos: {len(filas) - total_ok}", "",
              "| Caso | Regla | Resultado | Título |", "|---|---|---|---|"]
    for caso, difs in filas:
        lineas.append(f"| {caso['id']} | {caso.get('regla', '')} | {'OK' if not difs else 'DIFERENTE'} | {caso.get('titulo', '')} |")
    for caso, difs in filas:
        if difs:
            lineas += ["", f"## {caso['id']} · {caso.get('titulo', '')}", ""] + [f"- {d}" for d in difs[:40]]
    texto = "\n".join(lineas) + "\n"
    if a.reporte:
        open(a.reporte, "w", encoding="utf-8").write(texto)
    print(texto)
    return 0 if total_ok == len(filas) else 1


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    c = s.add_parser("capturar"); c.add_argument("--base", required=True); c.add_argument("--casos", required=True); c.add_argument("--salida", required=True); c.set_defaults(f=cmd_capturar)
    k = s.add_parser("comparar"); k.add_argument("--base", required=True); k.add_argument("--casos", required=True); k.add_argument("--referencia", required=True)
    k.add_argument("--reporte"); k.set_defaults(f=cmd_comparar)
    a = p.parse_args()
    sys.exit(a.f(a))


if __name__ == "__main__":
    main()
