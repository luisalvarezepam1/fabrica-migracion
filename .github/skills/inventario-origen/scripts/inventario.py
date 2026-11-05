#!/usr/bin/env python3
"""Inventario estático de una aplicación Python/Flask: rutas, tablas, constantes de negocio,
dependencias, pruebas y documentación. No ejecuta el código.

  python3 inventario.py --fuente fuente --salida corridas/<id>/artefactos/inventario
Genera inventario.json e inventario.md.
"""
import argparse
import ast
import json
import pathlib
import re

RUTA_RE = re.compile(r"@(\w+)\.(get|post|put|patch|delete|route)\(\s*[\"']([^\"']+)[\"'](?:[^)]*methods=\[([^\]]+)\])?")
PREFIJO_RE = re.compile(r"(\w+)\s*=\s*Blueprint\([^)]*url_prefix=[\"']([^\"']+)[\"']")
TABLA_RE = re.compile(r"CREATE TABLE IF NOT EXISTS (\w+) \((.*?)\);", re.S)
ERROR_RE = re.compile(r"ErrorNegocio\(\s*[\"'](\w+)[\"'][^)]*?(?:,\s*(\d{3}))?\)")


def constantes(arbol):
    out = []
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and len(nodo.targets) == 1 and isinstance(nodo.targets[0], ast.Name) and nodo.targets[0].id.isupper():
            try:
                valor = ast.unparse(nodo.value)
            except Exception:
                valor = "?"
            out.append({"nombre": nodo.targets[0].id, "valor": valor, "linea": nodo.lineno})
    return out


def funciones(arbol):
    return [{"nombre": n.name, "linea": n.lineno, "doc": (ast.get_docstring(n) or "").split("\n")[0]}
            for n in arbol.body if isinstance(n, ast.FunctionDef)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fuente", default="fuente")
    p.add_argument("--salida", required=True)
    a = p.parse_args()
    raiz = pathlib.Path(a.fuente)
    inv = {"rutas": [], "tablas": [], "modulos": [], "errores": {}, "dependencias": [], "pruebas": [], "documentos": []}
    prefijos = {}
    archivos = sorted(x for x in raiz.rglob("*.py") if ".venv" not in x.parts and "site-packages" not in x.parts)
    for f in archivos:
        t = f.read_text(encoding="utf-8")
        prefijos.update(dict(PREFIJO_RE.findall(t)))
    for f in archivos:
        rel = str(f.relative_to(raiz))
        t = f.read_text(encoding="utf-8")
        for bp, verbo, ruta, metodos in RUTA_RE.findall(t):
            ms = [m.strip(" '\"").upper() for m in metodos.split(",")] if metodos else ([verbo.upper()] if verbo != "route" else ["GET"])
            inv["rutas"].append({"metodos": ms, "ruta": prefijos.get(bp, "") + ruta, "blueprint": bp, "archivo": rel})
        for nombre, cols in TABLA_RE.findall(t):
            inv["tablas"].append({"tabla": nombre, "columnas": [c.strip().split()[0] for c in cols.split(",\n") if c.strip()], "archivo": rel})
        for codigo, http in ERROR_RE.findall(t):
            inv["errores"].setdefault(codigo, {"http": int(http) if http else 422, "archivos": set()})["archivos"].add(rel)
        if f.parent.name == "tests" or f.name.startswith("test_"):
            inv["pruebas"].append({"archivo": rel, "pruebas": len(re.findall(r"^def test_", t, re.M))})
            continue
        try:
            arbol = ast.parse(t)
        except SyntaxError:
            continue
        inv["modulos"].append({"archivo": rel, "doc": (ast.get_docstring(arbol) or "").split("\n")[0], "constantes": constantes(arbol), "funciones": funciones(arbol)})
    for req in raiz.glob("requirements*.txt"):
        inv["dependencias"] += [{"archivo": req.name, "paquete": l.strip()} for l in req.read_text().splitlines() if l.strip() and not l.startswith(("#", "-r"))]
    for d in list(raiz.glob("*.md")) + list(raiz.glob("docs/**/*.md")):
        inv["documentos"].append(str(d.relative_to(raiz)))
    inv["errores"] = {k: {"http": v["http"], "archivos": sorted(v["archivos"])} for k, v in sorted(inv["errores"].items())}

    salida = pathlib.Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.with_suffix(".json").write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# Inventario del origen", "", f"Fuente: `{raiz}` · {len(inv['rutas'])} rutas · {len(inv['tablas'])} tablas · {len(inv['errores'])} códigos de error · {sum(p['pruebas'] for p in inv['pruebas'])} pruebas", "",
          "## Rutas", "", "| Métodos | Ruta | Archivo |", "|---|---|---|"]
    md += [f"| {', '.join(r['metodos'])} | `{r['ruta']}` | {r['archivo']} |" for r in inv["rutas"]]
    md += ["", "## Tablas", ""] + [f"- **{t['tabla']}**: {', '.join(t['columnas'])}" for t in inv["tablas"]]
    md += ["", "## Constantes de negocio", ""]
    for m in inv["modulos"]:
        for c in m["constantes"]:
            md.append(f"- `{m['archivo']}:{c['linea']}` **{c['nombre']}** = `{c['valor']}`")
    md += ["", "## Códigos de error", "", "| Código | HTTP | Archivos |", "|---|---|---|"]
    md += [f"| {k} | {v['http']} | {', '.join(v['archivos'])} |" for k, v in inv["errores"].items()]
    md += ["", "## Dependencias", ""] + [f"- {d['paquete']} ({d['archivo']})" for d in inv["dependencias"]]
    md += ["", "## Pruebas existentes", ""] + [f"- {p['archivo']}: {p['pruebas']} pruebas" for p in inv["pruebas"]]
    md += ["", "## Documentación encontrada", ""] + [f"- {d}" for d in inv["documentos"]]
    md += ["", "> Este inventario es estático. Las reglas reales se confirman con las pruebas de caracterización contra el origen en ejecución."]
    salida.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Inventario: {len(inv['rutas'])} rutas, {len(inv['tablas'])} tablas -> {salida.with_suffix('.md')}")


if __name__ == "__main__":
    main()
