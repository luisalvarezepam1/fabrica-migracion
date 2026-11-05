---
name: jira-tareas
description: Crea la épica y las tareas de una migración en Jira Cloud, las mueve de estado y les agrega comentarios con evidencia. Funciona en modo local si no hay conexión configurada.
---
# Tareas en Jira

Script: [scripts/jira.py](scripts/jira.py) (solo Python estándar). Lee la conexión de `.env` en la raíz de la fábrica; **nunca leas ni muestres ese archivo**.

## Configuración (la hace la persona, no el agente)

Copiar `.env.example` a `.env` y completar `JIRA_URL`, `JIRA_EMAIL`, `JIRA_TOKEN` y `JIRA_PROYECTO`. Sin `.env`, el script trabaja en **modo local** (claves `LOCAL-n` y `artefactos/tablero-jira.md`).

## Formato de `plan-jira.json`

```json
{
  "epica": {"resumen": "Migración Transferencias Inmediatas a .NET 8", "descripcion": "Objetivo...\n- Solicitud: solicitudes/..."},
  "tareas": [
    {"ref": "T-ARQ", "etapa": "arquitectura", "resumen": "Arquitectura y diseño destino", "descripcion": "Cubre RNF-1, RNF-2\n- Criterio: ..."},
    {"ref": "T-MIG-transferencias", "etapa": "migracion", "resumen": "Migrar módulo de transferencias", "descripcion": "Cubre RN-1..RN-6\n- Criterio: ..."}
  ]
}
```

Las líneas que empiezan con `- ` se convierten en viñetas en Jira.

## Comandos

```bash
python3 .github/skills/jira-tareas/scripts/jira.py probar                       # conexión y proyecto
python3 .github/skills/jira-tareas/scripts/jira.py tipos                        # tipos de incidencia del proyecto
python3 .github/skills/jira-tareas/scripts/jira.py crear-plan corridas/<id>/artefactos/plan-jira.json
python3 .github/skills/jira-tareas/scripts/jira.py mover T-ARQ "En curso"       # acepta ref o clave
python3 .github/skills/jira-tareas/scripts/jira.py comentar T-ARQ "Diseño aprobado por ... · artefactos: ..."
```

- `mover` acepta el nombre de la transición o del estado destino, y traduce «Por hacer», «En curso», «En revisión» y «Listo» a sus equivalentes en inglés (To Do, In Progress, In Review, Done). Si no encuentra la transición, muestra las disponibles.
- El mapa ref → clave queda en `corridas/<id>/jira.json` y en `estado.json`.
