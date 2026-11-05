---
name: replay
description: Genera la repetición paso a paso (replay.html) de una corrida de la fábrica a partir de su bitácora, con etapas, agentes, artefactos, hallazgos y decisiones humanas.
---
# Replay de la corrida

```bash
python3 herramientas/fabrica.py replay
```

Genera `corridas/<id>/replay.html`, una página que se abre sin servidor.

- Lee `eventos.jsonl` y `estado.json`. Si un agente no registró sus eventos, el replay no los muestra: por eso cada agente registra inicio, artefactos, hallazgos, puertas y fin.
- Para cada puerta muestra quién decidió, con qué justificación y **cuánto tardó** desde que se pidió (`puerta.solicitada`) hasta que se resolvió. Una aprobación en menos de 30 segundos se marca como «¿aprobación sin leer?».
- Script: [scripts/replay.py](scripts/replay.py).
