---
name: reglas-de-dinero
description: Lista de verificación para código que mueve dinero (comisiones, impuestos, límites, idempotencia, reversos, auditoría). Úsala al diseñar, migrar o revisar operaciones financieras.
---
# Reglas de dinero

Cualquier incumplimiento es un hallazgo **alto**.

## Lista de verificación

- [ ] **Tipo exacto:** importes en `decimal` o enteros de centavos. Nunca `float`/`double`.
- [ ] **Redondeo explícito:** cada porcentaje indica el modo (por ejemplo «mitad hacia arriba») y se prueba con un monto que cae exactamente en medio centavo.
- [ ] **Orden de cobro:** comisión e impuesto se calculan y cobran **una sola vez**, dentro de la misma transacción que la operación, y **después** de todas las validaciones.
- [ ] **Idempotencia:** repetir una operación con la misma clave devuelve el resultado original **sin mover saldos otra vez**. Se prueba consultando el saldo después de cada repetición, no solo la respuesta.
- [ ] **Saldo suficiente** para monto + comisión + impuesto, validado antes de mover nada.
- [ ] **Límites** por cliente y moneda, en la **zona horaria del negocio**, con pruebas justo en el límite, un centavo arriba y al cambiar el día.
- [ ] **Reversos:** qué se devuelve y qué no (por ejemplo, la comisión), una sola vez, solo en el plazo permitido.
- [ ] **Atomicidad:** si algo falla, no queda ningún movimiento parcial.
- [ ] **Auditoría:** toda operación, exitosa o rechazada, deja rastro sin datos sensibles.
- [ ] **Formato:** los importes se presentan con dos decimales y cultura invariante.

## Preguntas que siempre se hacen

1. ¿Qué pasa si el cliente repite la operación por un timeout?
2. ¿Qué pasa a las 23:59 y a las 00:01 en la zona horaria del negocio?
3. ¿Qué pasa con un monto de 0.01 y con el máximo permitido?
4. ¿Las pruebas existentes del origen cubren estos casos, o solo los caminos felices?
