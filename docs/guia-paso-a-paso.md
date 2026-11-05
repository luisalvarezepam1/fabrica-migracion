# Guía paso a paso: correr la fábrica en VS Code

> **Nota:** los pasos 1 a 10 se documentaron con una primera corrida sobre la versión completa del origen (v1.4). La fábrica ahora corre en **modo taller**, con un módulo y su pantalla, y se está documentando con una corrida nueva. Los pasos son los mismos; cambian los tiempos y el tamaño de los artefactos.

Esta guía se arma con la primera corrida real de la fábrica. Cada paso dice qué hacer, qué debes ver y qué hacer si algo sale distinto.

## Antes de empezar

- VS Code reciente con GitHub Copilot iniciado con tu cuenta.
- Python 3.11+, .NET 8 SDK y Git. Terraform es opcional.
- Este repositorio clonado: `git clone https://github.com/luisalvarezepam1/fabrica-migracion.git`

## Paso 1 · Abrir la fábrica

1. **File › Open Folder…** y elige la carpeta `fabrica-migracion`. Debe ser la carpeta raíz.
2. Si VS Code pregunta si confías en los autores, elige **Trust**. Sin eso los agentes no pueden ejecutar comandos.

## Paso 2 · Preparar el chat

1. Abre el chat de Copilot (⌃⌘I en Mac, Ctrl+Alt+I en Windows).
2. Abajo a la izquierda, en el selector de harness, elige **Local**.
3. En el selector de agente, elige **Fabrica**. Deja el modelo en **Auto**: Copilot elige el modelo para cada tarea.
4. Deja los permisos en **Default permissions**. Así el agente te pide aprobar cada comando antes de ejecutarlo.

> **Si aparece «N workspace customizations need an update to keep working»:** elige **Ignore**. Ese aviso es del harness **Copilot**, que no carga los comandos (`*.prompt.md`) ni los botones entre etapas (handoffs). La fábrica se corre en **Local**, donde todo funciona tal como está en el repositorio. No uses **Migrate**: cambiaría tus archivos y dejaría de coincidir con el repositorio.

## Paso 3 · Confirmar que VS Code ve la fábrica

1. Paleta de comandos (⇧⌘P) › **Chat: Open Customizations**.
2. Debes ver:
   - **Agents:** 10 (Fabrica, Analista, Planificador, Arquitecto, Caracterizador, Migrador, Tester, Revisor, Plataforma y Bibliotecario).
   - **Skills:** 7 (pruebas-de-contrato, inventario-origen, jira-tareas, replay, python-a-dotnet, reglas-de-dinero y terraform-camino-dorado).
   - **Prompts:** 4 (iniciar-migracion, estado, verificar-ambiente y replay).

## Paso 4 · Jira (opcional)

**Sin Jira** no hagas nada. La fábrica crea las tareas en tu carpeta, en `corridas/<id>/tareas/`: un tablero por columnas y un archivo por tarea con su historial y sus comentarios.

**Con Jira**, en tu terminal:

```bash
cp .env.example .env
```

Completa `JIRA_URL`, `JIRA_EMAIL`, `JIRA_TOKEN` (créalo en https://id.atlassian.com/manage-profile/security/api-tokens) y `JIRA_PROYECTO`. El `.env` no se sube a GitHub y los agentes no lo leen: solo lo usa el script.

## Paso 5 · Verificar el ambiente

1. Con el agente **Fabrica** en **Local**, escribe `/verificar-ambiente` y envíalo.
2. El agente lee las reglas de la fábrica y la skill de Jira, y luego pide permiso para ejecutar **un solo comando**:
   ```
   python3 herramientas/fabrica.py verificar && python3 .github/skills/jira-tareas/scripts/jira.py probar
   ```
   Revisa que sea ese y da clic en **Allow**. Si pide algo distinto, como abrir o mostrar `.env`, elige **Skip**.
3. Resultado esperado:
   - Python, .NET SDK, Git y Terraform en `[OK]`.
   - Con `.env`: «Conectado a https://… como <tu nombre> · proyecto MIG (Fábrica de migración)».
   - Sin `.env`: «Modo local: no hay conexión a Jira configurada…». También es correcto.

**Primera corrida (5 de noviembre de 2026):** macOS Apple Silicon. Python 3.13, .NET 8.0.133, Git 2.54 y Terraform 1.15.6 en OK. Jira conectado al proyecto MIG. El agente se resolvió automáticamente con el modelo GPT-6 Luna, y ejecutó únicamente el comando de verificación.

## Paso 6 · Iniciar la corrida

1. Abre un chat nuevo (**+**). **Cada chat nuevo vuelve al harness Copilot:** antes de escribir, elige otra vez **Local**. Si no, `/iniciar-migracion` no aparece, porque el harness Copilot no carga los comandos.
2. Escribe y envía:
   ```
   /iniciar-migracion solicitudes/transferencias-inmediatas-a-dotnet.md
   ```
   El comando cambia solo al agente **Fabrica**.
3. Aprueba solo estos comandos: `fabrica.py verificar`, `fabrica.py iniciar …`, `jira.py probar` y `fabrica.py estado`.
4. Resultado esperado:
   - una corrida nueva, `corridas/MIG-<fecha>-<hora>/`, con `solicitud.md`, `estado.json` y `eventos.jsonl`;
   - la carpeta `fuente/` con la app de origen en Python;
   - la tabla de estado: 9 etapas pendientes y 5 puertas humanas;
   - el botón **«1 · Analizar el requerimiento»**.

> **Sin el comando:** si `/iniciar-migracion` no aparece, elige el agente **Fabrica** y escribe: «Inicia una corrida de la fábrica con la solicitud solicitudes/transferencias-inmediatas-a-dotnet.md. Verifica el ambiente, inicia la corrida, prueba Jira y muéstrame el estado. No avances a la siguiente etapa».

**Primera corrida:** corrida `MIG-20261104-224342`. El origen se clonó en `fuente/` y quedaron las 9 etapas pendientes. Las tareas de Jira todavía no se crean: eso lo hace el Planificador en la etapa 2.

## Paso 7 · Etapa 1: análisis del requerimiento (Analista)

1. Da clic en **«1 · Analizar el requerimiento»**. El agente cambia a **Analista** y deja el mensaje escrito; envíalo.
2. Aprueba los comandos `fabrica.py evento …` (y `fabrica.py hallazgo …` si aparecen). El agente lee la solicitud, el catálogo y `fuente/`.
3. Escribe `corridas/<id>/artefactos/analisis.md`. Da clic en **Keep** para conservarlo.
4. **Puerta del líder.** El agente pregunta «¿Apruebas el análisis? Indica tu nombre y, si hay cambios, cuáles». Antes de responder, **lee el análisis**: resumen, requisitos `RF/RNF`, reglas `RN`, riesgos y **preguntas abiertas**. Responde con tu nombre, tu decisión y las respuestas a las preguntas abiertas.
5. El agente agrega tus respuestas al análisis como «Acuerdos de aprobación», registra la puerta con tu nombre y cierra la etapa.

**Primera corrida:** 4 requisitos funcionales, 5 no funcionales, 8 reglas de negocio, 7 riesgos y 3 preguntas abiertas. Las preguntas fueron: dónde se pueden hacer pruebas que cambian datos, qué perfil de carga usar para el p95 y qué Application Insights usar. Respuestas del líder: las pruebas que cambian datos van solo contra el origen local, y contra Azure solo lecturas (GET); 50 llamadas secuenciales y 5 concurrentes; el Application Insights que crea el módulo aprobado. La puerta se resolvió en unos 5 minutos, y con las respuestas el Analista agregó un riesgo nuevo: la equivalencia entre local y producción.

## Paso 8 · Etapa 2: plan en Jira (Planificador)

1. Da clic en **Keep** para conservar los cambios del análisis y luego en **«2 · Crear el plan de trabajo»**. El agente cambia a **Planificador**; envía el mensaje.
2. Aprueba `fabrica.py estado`, `fabrica.py evento …` y `jira.py crear-plan …`. Da **Keep** a `plan-jira.json`.
3. Resultado:
   - **Con `.env`:** una épica y sus tareas en Jira, más un espejo en `corridas/<id>/tareas/` con `tablero.md` y un archivo por tarea con enlace a Jira.
   - **Sin `.env`:** las mismas tareas como `LOCAL-n` en `corridas/<id>/tareas/`, con su tablero por columnas.

**Primera corrida:** épica **MIG-1** y 14 tareas, creadas en unos 3 minutos:

- 6 tareas de etapa: arquitectura, caracterización, pruebas, revisión, plataforma y documentación;
- 8 tareas de migración, una por módulo: clientes, cuentas, movimientos, transferencias, reversos, auditoría, modo demo y pantallas.

Cada descripción indica qué requisitos `RF/RNF/RN` cubre y su criterio de aceptación.

## Paso 9 · Etapa 3: arquitectura (Arquitecto)

1. Da clic en **«3 · Diseñar la arquitectura»** y envía el mensaje. La tarea de arquitectura pasa a **En curso** en Jira o en el tablero local.
2. Aprueba `inventario.py …`, `fabrica.py evento …`, `fabrica.py hallazgo …` y `jira.py mover/comentar …`. Da **Keep** a: `inventario.md/json`, `arquitectura.md`, `adr-001-stack.md`, `mapeo-origen-destino.md` y `plan-de-pruebas.md`.
3. **Puerta del arquitecto.** Lee el diseño y, sobre todo, **los hallazgos**. Si hay hallazgos altos abiertos, la herramienta exige una justificación escrita para aprobar: explica por qué apruebas igual (por ejemplo, porque los decide el negocio en la etapa 4).

**Primera corrida (unos 7 minutos):** solo leyendo el código, el Arquitecto encontró 4 hallazgos:

- **H01 (alto):** la documentación dice límite diario DOP 300,000 y el código aplica 500,000. Además, la prueba existente no distingue entre los dos valores.
- **H02 (alto):** una repetición idempotente vuelve a cobrar la comisión, porque se cobra antes de revisar la clave. La prueba existente no lo detecta porque usa una transferencia propia, sin comisión.
- **H03 (alto):** hay un máximo por operación sin documentar.
- **H04 (medio):** la API devuelve HTTP 405, que no está documentado.

También señaló que `Math.Round` redondea al par y fijó `MidpointRounding.AwayFromZero`. El diseño se aprobó con justificación, y los hallazgos quedaron abiertos para el dueño de negocio.

## Paso 10 · Etapa 4: caracterización del origen (Caracterizador)

> **macOS:** el puerto 5000 lo ocupa AirPlay Receiver. El origen se levanta en el **5050** y el destino en el **5080**.

1. Da clic en **«4 · Caracterizar el origen»** y envía el mensaje.
2. Aprueba la creación del entorno (`python3 -m venv .venv-fuente`, `pip install -r fuente/requirements.txt`), el arranque del origen en `127.0.0.1:5050`, las llamadas `curl` locales y `contrato.py capturar --base http://127.0.0.1:5050 …`. **Elige Skip** si ves un `POST` o un `capturar` contra la URL de Azure, o cualquier cosa en el puerto 5000.
3. Da **Keep** a `casos.json`, `referencia.json` y `caracterizacion.md`.
4. **Puerta del dueño de negocio.** El agente presenta cada hallazgo con su evidencia y dos opciones: **preservar** o **corregir**. Decide uno por uno. Para lo que decidas corregir, el agente agrega un resultado `esperado` en `casos.json`, y ese resultado lo exigirá el Tester al destino.

**Primera corrida (unos 17 minutos):** 35 casos y 151 pasos contra el origen local. La referencia confirmó con datos los cuatro hallazgos:

- **H01:** DOP 300,000.01 pasa y el límite real es 500,000.
- **H02:** la repetición devuelve la misma transferencia, pero baja el saldo DOP 10.00 y crea un movimiento de comisión nuevo.
- **H03:** el máximo de DOP 10,000,000.00 existe.
- **H04:** el 405 en JSON existe.

Decisiones del negocio: **preservar** H01, H03 y H04 (y documentarlos), y **corregir** H02. En el caso de H02, los pasos 6 y 7 tienen ahora como `esperado` el saldo y los movimientos sin la segunda comisión. Al terminar, el agente detuvo el origen local.

## Paso 11 · Etapa 5: migración del código (Migrador)

_En curso._
