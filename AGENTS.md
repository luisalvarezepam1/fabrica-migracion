# Reglas de la fábrica de migración

Estas reglas aplican a **todos** los agentes de la fábrica (`.github/agents/`) y a cualquier agente que trabaje en este repositorio.

## Qué es esto

Una fábrica de agentes que recibe una **solicitud de migración** escrita por un líder (`solicitudes/*.md`), la analiza, planifica el trabajo en Jira, diseña el destino, caracteriza el sistema de origen, lo migra al stack pedido, prueba que se comporte igual, revisa seguridad y reglas de dinero, prepara la infraestructura con módulos aprobados y documenta todo en un replay.

## Estructura del espacio de trabajo

| Carpeta | Qué contiene | Regla |
|---|---|---|
| `solicitudes/` | Solicitudes de migración de los líderes | Solo lectura para los agentes |
| `fuente/` | Clon del sistema de origen | **Solo lectura.** Nunca modificar |
| `destino/` | El sistema migrado que construye la fábrica | Lo escriben Migrador y Plataforma |
| `corridas/<id>/` | Estado, eventos, artefactos y replay de cada corrida | Todo lo que produce un agente va en `artefactos/` |
| `catalogo/` | Stacks aprobados | La fábrica solo migra a stacks del catálogo |
| `plataforma/` | Módulos de Terraform y pipelines aprobados («camino dorado») | Se copian y se ajustan variables; no se reescriben |
| `herramientas/` | `fabrica.py` (corridas, eventos, puertas, hallazgos, replay) | |

## Reglas obligatorias

1. **Idioma:** español en artefactos, mensajes y commits. Código e identificadores pueden ir en inglés si el stack destino lo acostumbra.
2. **Datos ficticios.** Nunca uses datos reales de clientes, cuentas ni personas.
3. **Secretos:** nunca leas, imprimas, copies ni registres el contenido de `.env`, tokens, contraseñas o llaves. Los scripts los leen por su cuenta. Si un comando mostraría un secreto, no lo ejecutes.
4. **Bitácora:** cada etapa empieza y termina con un evento, y cada artefacto se registra:
   ```bash
   python3 herramientas/fabrica.py evento --etapa <etapa> --agente <Agente> --tipo etapa.iniciada --resumen "..."
   python3 herramientas/fabrica.py evento --etapa <etapa> --agente <Agente> --tipo artefacto --resumen "..." --archivo corridas/<id>/artefactos/<archivo>
   python3 herramientas/fabrica.py evento --etapa <etapa> --agente <Agente> --tipo etapa.terminada --resumen "..."
   ```
5. **Puertas humanas.** Donde tu etapa tiene puerta, **no la apruebes tú**. Registra que la pides, presenta un resumen claro con lo que la persona debe revisar y **espera su respuesta en el chat**. Solo entonces registra la decisión con el nombre de quien decidió:
   ```bash
   python3 herramientas/fabrica.py evento --etapa <etapa> --agente <Agente> --tipo puerta.solicitada --resumen "Qué se debe revisar"
   python3 herramientas/fabrica.py puerta --etapa <etapa> --rol "<Rol>" --decision aprobado|rechazado|cambios --por "<Nombre>" --justificacion "<lo que dijo>"
   ```
   Si hay hallazgos **altos** abiertos, la herramienta exige una justificación escrita para aprobar. No la inventes: pídela.
6. **Hallazgos.** Toda diferencia entre documentación y comportamiento, defecto heredado, riesgo de seguridad o de dinero se registra:
   ```bash
   python3 herramientas/fabrica.py hallazgo --etapa <etapa> --agente <Agente> --severidad alta|media|baja --titulo "..." --detalle "..."
   ```
   **El comportamiento observado manda sobre la documentación**, pero la diferencia siempre se reporta. Un defecto heredado **no se copia ni se corrige en silencio**: se reporta y decide una persona.
7. **Jira.** Cada agente mueve y comenta su tarea con `.github/skills/jira-tareas/scripts/jira.py` (sin `.env` funciona en modo local).
8. **Acciones irreversibles o externas** (`git push`, `terraform apply`, `az`, crear repos, despliegues): **nunca** sin una confirmación explícita de la persona en el chat. Los participantes del workshop solo corren el destino en local.
9. **Dinero:** importes con tipo decimal exacto (nunca `float`/`double`), redondeo explícito y documentado, idempotencia que no cobre dos veces y límites probados en la zona horaria del negocio. Ver la skill `reglas-de-dinero`.
10. **Fuera de alcance o de catálogo:** si la solicitud pide algo que no está en `catalogo/stacks.md` o que no se puede cumplir, detente y explícalo. No improvises un stack.
11. **Evidencia antes que opinión:** cada afirmación de un artefacto debe poder rastrearse a un archivo, una prueba o una salida de comando.

## Etapas y agentes

| # | Etapa | Agente | Puerta humana |
|---|---|---|---|
| 1 | `analisis` | Analista | Líder solicitante aprueba el análisis |
| 2 | `plan` | Planificador | — |
| 3 | `arquitectura` | Arquitecto | Arquitecto responsable aprueba el diseño |
| 4 | `caracterizacion` | Caracterizador | Dueño de negocio decide sobre los hallazgos (preservar o corregir) |
| 5 | `migracion` | Migrador | — |
| 6 | `pruebas` | Tester | — (si hay diferencias, vuelve a Migrador) |
| 7 | `revision` | Revisor | Riesgo / Seguridad aprueba |
| 8 | `plataforma` | Plataforma | Comité de cambios aprueba la entrega |
| 9 | `aprendizaje` | Bibliotecario | — |

El orquestador es el agente **Fabrica**: inicia la corrida y muestra el estado (`python3 herramientas/fabrica.py estado`).
