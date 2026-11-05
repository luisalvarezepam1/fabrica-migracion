# Guía paso a paso: correr la fábrica en VS Code

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

_En curso._
