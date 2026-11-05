# Fábrica de migración con agentes (GitHub Copilot)

Una fábrica de agentes que corre en **VS Code con GitHub Copilot**. Recibe una solicitud de migración escrita por un líder, la analiza, planifica el trabajo en Jira, diseña el destino, caracteriza el sistema de origen, lo migra, prueba que se comporte igual, revisa seguridad y reglas de dinero, prepara la infraestructura con módulos aprobados y deja un **replay** de todo lo que pasó.

El caso de ejemplo migra [Transferencias Inmediatas](https://github.com/luisalvarezepam1/banco-transferencias-legado), una app de un banco ficticio en Python/Flask, a **.NET 8 en Azure App Service**. El resultado de referencia vive en [banco-transferencias-net](https://github.com/luisalvarezepam1/banco-transferencias-net).

> Todos los datos son ficticios.

## Cómo funciona

```
solicitud.md ─► Analista ─► Planificador ─► Arquitecto ─► Caracterizador ─► Migrador ◄─► Tester ─► Revisor ─► Plataforma ─► Bibliotecario
                  │              │              │                │                                    │            │              │
             [Líder aprueba]   Jira      [Arquitecto]     [Negocio decide                        [Riesgo]      [CAB]        replay.html
                                                           sobre hallazgos]
```

| Pieza | Dónde |
|---|---|
| Reglas para todos los agentes | [AGENTS.md](AGENTS.md) |
| 10 agentes con handoffs (botones entre etapas) | [.github/agents/](.github/agents/) |
| 7 skills con scripts (contrato, inventario, Jira, replay, Python→.NET, dinero, Terraform) | [.github/skills/](.github/skills/) |
| Comandos `/iniciar-migracion`, `/estado`, `/verificar-ambiente`, `/replay` | [.github/prompts/](.github/prompts/) |
| Plantilla de solicitud y ejemplo | [plantillas/](plantillas/), [solicitudes/](solicitudes/) |
| Stacks aprobados | [catalogo/stacks.md](catalogo/stacks.md) |
| Módulo de Terraform y pipeline aprobados | [plataforma/](plataforma/) |
| Corridas, eventos, puertas y hallazgos | [herramientas/fabrica.py](herramientas/fabrica.py) → `corridas/<id>/` |

Cada etapa termina con un botón para pasar a la siguiente. Las **puertas humanas** no las aprueba un agente: el agente presenta lo que hay que revisar, tú respondes en el chat con tu nombre y tu decisión, y queda registrado. Si hay un hallazgo **alto** abierto, aprobar exige una justificación escrita.

## Modo taller (una hora)

La solicitud de ejemplo está en **modo taller**: migra un solo módulo (transferencias, con su pantalla web) y los agentes trabajan con límites de tiempo. Por ejemplo: artefactos breves, de 10 a 14 casos de contrato, la plantilla .NET aprobada en lugar de crear proyectos y como máximo dos ciclos de corrección. La corrida completa, con las 9 etapas y las 5 puertas, está pensada para alrededor de una hora.

## Dónde correrla

| Opción | Para quién | Qué necesitas |
|---|---|---|
| **GitHub Codespaces** (recomendada en Windows o en laptops sin permisos de administrador) | Cualquier participante con GitHub Copilot | Una cuenta de GitHub con Copilot y acceso a github.com. En el repo: **Code › Codespaces › Create codespace on main**. El ambiente ya trae Python, .NET 8 y Terraform |
| **VS Code local en macOS, Linux o Windows** | Quien pueda instalar herramientas | Python 3.11+, .NET 8 SDK y Git. En Windows: `winget install Python.Python.3.12 Microsoft.DotNet.SDK.8 Git.Git`, y usa `python` en lugar de `python3` |

Los agentes levantan y detienen el origen y el destino con `fabrica.py origen|destino iniciar|detener`, que funciona igual en los tres sistemas. Antes del workshop conviene correr `fabrica.py preparar` para descargar las dependencias.

## Preparación

1. **VS Code** reciente con **GitHub Copilot** iniciado con tu cuenta (cualquier plan con modo agente).
2. **Python 3.11+**, **.NET 8 SDK** y **Git**. Terraform 1.9+ es opcional (para validar la infraestructura).
3. Clona este repositorio y ábrelo como carpeta raíz en VS Code.
4. (Opcional) Jira: copia `.env.example` a `.env` y completa tus datos. Sin `.env`, la fábrica usa un tablero local.
5. En el chat de Copilot elige el harness **Local** (los handoffs funcionan ahí) y ejecuta `/verificar-ambiente`.

> Si tu laptop no permite instalar herramientas, abre el repositorio en **GitHub Codespaces**.

## Correr la fábrica

La guía detallada, con lo que debes ver en cada paso, está en [docs/guia-paso-a-paso.md](docs/guia-paso-a-paso.md).


1. En el chat, elige el agente **Fabrica** y escribe `/iniciar-migracion`.
2. Sigue los botones: **1 · Analizar el requerimiento**, **2 · Crear el plan de trabajo**, y así hasta **9 · Documentar y generar el replay**.
3. En cada puerta, lee lo que te muestra el agente **antes** de aprobar. El replay mide cuánto tardaste.
4. Al final abre `corridas/<id>/replay.html` en tu navegador.

El destino queda en `destino/`. Para correrlo:

```bash
dotnet run --project destino/src/Transferencias.Api --urls http://127.0.0.1:5080
```

## Reglas de seguridad de la fábrica

- `fuente/` es de solo lectura. Nada de datos reales ni secretos.
- Los agentes **nunca** leen `.env` ni ejecutan `git push`, `terraform apply`, `az` o despliegues sin tu confirmación explícita.
- La infraestructura solo usa el módulo aprobado. El despliegue real lo hace el pipeline del repositorio de destino, con su propia aprobación del comité de cambios.

## Costo de una corrida

`python3 herramientas/fabrica.py costo` suma, desde el historial local de VS Code, los tokens de entrada y salida y los créditos de Copilot de cada agente desde que empezó la corrida, y estima el costo en USD (variable `FABRICA_USD_POR_CREDITO`, 0.01 por defecto). El replay muestra el total y el costo por etapa. Es una estimación: compárala con GitHub › Settings › Billing › Usage.

## Uso de premium requests

Cada etapa consume solicitudes del plan de Copilot de quien la corre. Para ahorrar, usa un modelo de costo bajo en las etapas sencillas (Planificador, Bibliotecario) y uno más capaz en Arquitecto, Migrador y Revisor.
