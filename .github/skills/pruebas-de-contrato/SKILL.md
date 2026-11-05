---
name: pruebas-de-contrato
description: Pruebas de contrato HTTP de caja negra para migraciones. Captura el comportamiento del origen como referencia (golden master) y compara el destino contra ella. Úsala para caracterizar un sistema, probar equivalencia o validar un despliegue en staging.
---
# Pruebas de contrato

Script: [scripts/contrato.py](scripts/contrato.py) (solo Python estándar).

## Cuándo usarla

- **Caracterizar** el origen antes de migrar (Caracterizador).
- **Probar equivalencia** del destino contra el origen (Tester).
- **Validar staging** en el pipeline antes del swap (Plataforma).

## Formato de `casos.json`

```json
{
  "ignorar": ["fecha", "fecha_reverso", "ahora"],
  "cabeceras": ["Idempotent-Replay"],
  "casos": [
    {
      "id": "C01",
      "titulo": "Terceros: impuesto con medio centavo (1670.00 -> 2.51)",
      "regla": "RN-03",
      "pasos": [
        {"reiniciar": true},
        {"metodo": "POST", "ruta": "/api/transferencias",
         "cabeceras": {"X-Demo-Ahora": "2026-11-05T10:00:00-04:00"},
         "cuerpo": {"cuenta_origen": "7001-0001", "cuenta_destino": "7001-0003", "monto": "1670.00"},
         "guardar": {"tid": "id"}},
        {"metodo": "GET", "ruta": "/api/transferencias/{tid}"},
        {"metodo": "GET", "ruta": "/api/cuentas/7001-0001"}
      ]
    }
  ]
}
```

- `reiniciar` llama a `POST /api/demo/reiniciar` para empezar cada caso desde los mismos datos.
- `guardar` toma un valor de la respuesta (ruta con puntos, p. ej. `id` o `0.numero`) y lo usa después como `{nombre}`.
- `ignorar` reemplaza campos volátiles por `<volátil>` en cualquier nivel.
- `esperado` en un paso (`{"estado": 200, "cuerpo": {...}}`) reemplaza la referencia del origen. **Solo** se agrega cuando el dueño de negocio decidió corregir un comportamiento del origen.

## Antes de capturar

Confirma que `--base` responde `GET /api/salud` con `"estado": "ok"`. En macOS el puerto 5000 lo ocupa AirPlay Receiver: usa 5050 para el origen y 5080 para el destino.

## Buenas prácticas

- Verifica **efectos**, no solo respuestas: después de cada operación consulta saldos y movimientos.
- Incluye montos que generen **medio centavo**, valores **en el límite** y **un centavo por encima**, cambios de **día en la zona horaria del negocio**, y **repeticiones** de la misma operación.
- Un caso por regla de negocio y por código de error del inventario.

## Comandos

```bash
python3 .github/skills/pruebas-de-contrato/scripts/contrato.py capturar --base http://127.0.0.1:5050 \
  --casos corridas/<id>/artefactos/pruebas-contrato/casos.json \
  --salida corridas/<id>/artefactos/pruebas-contrato/referencia.json

python3 .github/skills/pruebas-de-contrato/scripts/contrato.py comparar --base http://127.0.0.1:5080 \
  --casos corridas/<id>/artefactos/pruebas-contrato/casos.json \
  --referencia corridas/<id>/artefactos/pruebas-contrato/referencia.json \
  --reporte corridas/<id>/artefactos/reporte-equivalencia.md
```

`comparar` termina con código 1 si hay diferencias.
