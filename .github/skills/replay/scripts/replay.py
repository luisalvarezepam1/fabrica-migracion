#!/usr/bin/env python3
"""Genera corridas/<id>/replay.html: la repetición paso a paso de una corrida de la fábrica,
con etapas, agentes, artefactos, hallazgos y decisiones humanas (y cuánto tardó cada decisión).

  python3 herramientas/fabrica.py replay
"""
import datetime as dt
import html
import json
import pathlib


def _t(s):
    try:
        return dt.datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def _dur(seg):
    if seg is None:
        return ""
    seg = int(seg)
    return f"{seg} s" if seg < 90 else f"{seg // 60} min {seg % 60:02d} s"


def generar(corrida, etapas):
    corrida = pathlib.Path(corrida)
    est = json.loads((corrida / "estado.json").read_text(encoding="utf-8"))
    eventos = [json.loads(l) for l in (corrida / "eventos.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    inicio = _t(eventos[0]["ts"]) if eventos else None
    fin = _t(eventos[-1]["ts"]) if eventos else None
    e = html.escape

    solicitadas = {}
    filas = []
    for ev in eventos:
        t = _t(ev["ts"])
        rel = _dur((t - inicio).total_seconds()) if t and inicio else ""
        tipo = ev.get("tipo", "")
        extra = ""
        clase = tipo.split(".")[0]
        if tipo == "puerta.solicitada":
            solicitadas[ev.get("etapa")] = t
        if tipo == "puerta.resuelta":
            desde = solicitadas.get(ev.get("etapa"))
            espera = (t - desde).total_seconds() if t and desde else None
            alerta = espera is not None and espera < 30
            extra = (f"<div class='puerta {'rapida' if alerta else ''}'><b>{e(ev.get('decision', '').upper())}</b> por {e(ev.get('por', ''))} ({e(ev.get('rol', ''))})"
                     f"{' · decidió en ' + _dur(espera) if espera is not None else ''}"
                     f"{' · <b>¿aprobación sin leer?</b>' if alerta else ''}"
                     f"{'<br>Justificación: ' + e(ev['justificacion']) if ev.get('justificacion') else ''}"
                     f"{'<br>Hallazgos altos abiertos: ' + str(ev['hallazgos_altos_abiertos']) if ev.get('hallazgos_altos_abiertos') else ''}</div>")
        if ev.get("archivo"):
            extra += f"<div class='arch'>📄 <a href='{e(ev['archivo'])}'>{e(ev['archivo'])}</a></div>"
        if ev.get("jira"):
            extra += f"<div class='arch'>Jira: {e(ev['jira'])}</div>"
        filas.append(f"<li class='ev {e(clase)}'><span class='ts'>+{rel}</span><span class='et'>{e(ev.get('etapa', ''))}</span>"
                     f"<span class='ag'>{e(ev.get('agente', ''))}</span><span class='ti'>{e(tipo)}</span><div class='re'>{e(ev.get('resumen', '') or '')}</div>{extra}</li>")

    carril = "".join(
        f"<div class='etapa {e(est['etapas'][k]['estado'])}'><b>{e(n)}</b><span>{e(ag)}</span><span class='est'>{e(est['etapas'][k]['estado'].replace('_', ' '))}</span>"
        f"{'<span class=rol>Puerta: ' + e(rol) + '</span>' if rol else ''}</div>"
        for k, n, ag, rol in etapas)
    hall = "".join(f"<tr><td>{e(h['id'])}</td><td class='sev {e(h['severidad'])}'>{e(h['severidad'])}</td><td>{e(h['etapa'])}</td><td>{e(h['titulo'])}</td><td>{e(h['estado'])}{' · ' + e(h.get('resolucion', '')) if h.get('resolucion') else ''}</td></tr>"
                   for h in est.get("hallazgos", [])) or "<tr><td colspan='5'>Sin hallazgos.</td></tr>"
    jira = est.get("jira") or {}
    jira_html = (f"<p>Jira ({e(jira.get('modo', ''))}): épica <b>{e(str(jira.get('epica')))}</b> · {len(jira.get('tareas', {}))} tareas"
                 f"{' · <a href=' + e(jira['url']) + '>abrir</a>' if jira.get('url') else ''}</p>") if jira else ""
    puertas = est.get("puertas", [])
    total = _dur((fin - inicio).total_seconds()) if inicio and fin else ""

    pagina = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Replay {e(est['id'])}</title><style>
:root{{--f:#0f172a;--d:#64748b;--b:#e2e8f0;--a:#2563eb;--ok:#15803d;--al:#b45309;--er:#b91c1c}}
*{{box-sizing:border-box}}body{{margin:0;font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--f);background:#f8fafc}}
header{{background:#0f2a4a;color:#fff;padding:20px 24px}}header h1{{margin:0;font-size:20px}}header p{{margin:4px 0 0;opacity:.8}}
main{{max-width:1180px;margin:0 auto;padding:20px}}h2{{font-size:16px;margin:24px 0 10px}}
.kpis{{display:flex;gap:12px;flex-wrap:wrap}}.kpi{{background:#fff;border:1px solid var(--b);border-radius:10px;padding:10px 14px;min-width:140px}}.kpi b{{display:block;font-size:20px}}
.carril{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}}
.etapa{{background:#fff;border:1px solid var(--b);border-radius:10px;padding:10px;display:grid;gap:2px;font-size:12px}}.etapa b{{font-size:13px}}
.etapa.terminada{{border-color:#86efac;background:#f0fdf4}}.etapa.en_curso{{border-color:#93c5fd;background:#eff6ff}}.etapa.bloqueada{{border-color:#fca5a5;background:#fef2f2}}
.est{{font-weight:600;text-transform:uppercase;font-size:11px;color:var(--d)}}.rol{{color:var(--al)}}
ol{{list-style:none;padding:0;margin:0;border-left:2px solid var(--b)}}
.ev{{position:relative;margin:0 0 10px 14px;background:#fff;border:1px solid var(--b);border-radius:10px;padding:8px 12px;display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline}}
.ev:before{{content:"";position:absolute;left:-21px;top:14px;width:10px;height:10px;border-radius:50%;background:var(--a)}}
.ev.puerta:before{{background:var(--al)}}.ev.hallazgo:before{{background:var(--er)}}
.ts{{font-variant-numeric:tabular-nums;color:var(--d);font-size:12px;min-width:70px}}.et{{font-weight:600}}.ag{{color:var(--a)}}.ti{{font-size:11px;color:var(--d)}}
.re{{flex-basis:100%}}.arch{{flex-basis:100%;font-size:12px}}
.puerta{{flex-basis:100%;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:6px 10px}}.puerta.rapida{{background:#fef2f2;border-color:#fca5a5}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--b);border-radius:10px;overflow:hidden}}td,th{{padding:6px 10px;border-bottom:1px solid var(--b);text-align:left}}
.sev.alta{{color:var(--er);font-weight:700}}.sev.media{{color:var(--al);font-weight:600}}
</style></head><body>
<header><h1>Replay · {e(est['titulo'])}</h1><p>{e(est['id'])} · inicio {e(est.get('inicio', ''))}</p></header><main>
<div class="kpis"><div class="kpi"><b>{total}</b>duración</div><div class="kpi"><b>{len(eventos)}</b>eventos</div>
<div class="kpi"><b>{len(puertas)}</b>decisiones humanas</div><div class="kpi"><b>{len(est.get('hallazgos', []))}</b>hallazgos</div></div>
{jira_html}<h2>Etapas</h2><div class="carril">{carril}</div>
<h2>Hallazgos</h2><table><tr><th>Id</th><th>Severidad</th><th>Etapa</th><th>Título</th><th>Estado</th></tr>{hall}</table>
<h2>Línea de tiempo</h2><ol>{''.join(filas)}</ol>
<p style="color:var(--d);font-size:12px;margin-top:24px">Generado por la fábrica de migración a partir de eventos.jsonl. Datos ficticios.</p>
</main></body></html>"""
    salida = corrida / "replay.html"
    salida.write_text(pagina, encoding="utf-8")
    return salida
