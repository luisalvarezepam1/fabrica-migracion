# Instrucciones del repositorio

Este repositorio es una **fábrica de migración con agentes**. Antes de actuar, lee y sigue [AGENTS.md](../AGENTS.md): estructura de carpetas, bitácora, puertas humanas, hallazgos, Jira, secretos y reglas de dinero.

- Responde y escribe artefactos en español.
- `fuente/` es de solo lectura. El código nuevo va en `destino/`. Los artefactos de cada corrida van en `corridas/<id>/artefactos/`.
- Nunca leas ni muestres `.env` ni ningún secreto.
- Nunca ejecutes `git push`, `terraform apply`, `az` ni despliegues sin la confirmación explícita de la persona.
- Para empezar una migración, usa el agente **Fabrica** o el comando `/iniciar-migracion`.
