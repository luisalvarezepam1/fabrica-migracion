---
name: inventario-origen
description: Inventario estático de una aplicación Python/Flask (rutas, tablas, constantes de negocio, códigos de error, dependencias, pruebas y documentación). Úsala al inicio del diseño de una migración.
---
# Inventario del origen

Script: [scripts/inventario.py](scripts/inventario.py).

```bash
python3 .github/skills/inventario-origen/scripts/inventario.py --fuente fuente --salida corridas/<id>/artefactos/inventario
```

Genera `inventario.json` e `inventario.md`.

## Cómo leerlo

- El inventario es **estático**: dice qué hay en el código, no cómo se comporta. Las reglas se confirman con `pruebas-de-contrato`.
- Compara cada constante de negocio con lo que dice la documentación. **Cada diferencia es un hallazgo.**
- Lee el orden de las operaciones dentro de cada transacción (qué se cobra, qué se valida y en qué orden). Muchos defectos heredados viven ahí.
- Revisa qué cubren las pruebas existentes y qué **no** cubren: ahí se esconden los comportamientos que nadie verificó.
