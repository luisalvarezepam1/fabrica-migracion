# Solicitud de migración: Transferencias Inmediatas

## 1. Datos generales

- **Solicitante:** Gerente de Canales Digitales (ficticio)
- **Fecha:** 2026-11-05
- **Sistema:** Transferencias Inmediatas v2.0, módulo de transferencias (legado)
- **Repositorio de origen:** https://github.com/luisalvarezepam1/banco-transferencias-legado.git
- **URL del origen en ejecución (opcional):** https://app-bancolegado-439f6a.azurewebsites.net
- **Modo:** taller (un módulo, corrida completa en alrededor de una hora)

## 2. Objetivo

El módulo de transferencias corre en Python y el equipo que lo construyó ya no está. La estrategia de tecnología pide llevar los servicios del canal digital a .NET 8, que es el stack que el banco sabe operar y monitorear. La migración no debe cambiar lo que ven los clientes ni los cargos que se cobran.

## 3. Stack destino

- **Stack del catálogo:** dotnet8-appservice
- **Repositorio de destino:** https://github.com/luisalvarezepam1/banco-transferencias-net

## 4. Alcance

- **Incluye:** la API `/api` del módulo (salud, cuentas, transferencias y reinicio en modo demo) y la pantalla web en `/`.
- **No incluye:** otros módulos del banco, migración de datos históricos (el destino arranca con los mismos datos de ejemplo) ni autenticación de usuarios.

## 5. Requisitos funcionales

1. El destino expone **el mismo contrato de API**: rutas, códigos HTTP, códigos de error, nombres de campos y formato de los importes.
2. Las reglas de comisión, impuesto, límite diario e idempotencia se comportan **igual que en producción hoy**.
3. La pantalla web permite ver las cuentas, transferir y ver el historial; el diseño puede mejorar.

## 6. Requisitos no funcionales

- Tiempo de respuesta p95 menor a 300 ms en la API con los datos de ejemplo.
- Despliegue sin caída: primero a un slot de staging y, después de la aprobación, swap a producción.
- Observabilidad con Application Insights.
- Nada de secretos en el código ni en la configuración.

## 7. Restricciones y reglas de negocio críticas

- Los importes son exactos: no se aceptan diferencias de un centavo contra el sistema actual.
- El límite diario se calcula con el día de Santo Domingo.
- El modo demo (`X-Demo-Ahora` y `/api/demo/reiniciar`) se conserva para poder probar.

## 8. Criterios de aceptación

1. Todas las pruebas de contrato capturadas contra el origen pasan contra el destino, salvo las diferencias que apruebe el dueño de negocio por escrito.
2. Las pruebas unitarias del destino cubren comisión, impuesto, redondeo, límite diario e idempotencia.
3. El análisis de seguridad no tiene hallazgos altos abiertos.
4. La infraestructura usa solo módulos aprobados y pasa `terraform validate`.

## 9. Defectos conocidos y decisiones

- No conocemos defectos abiertos. Si la fábrica encuentra alguno, **no lo copia ni lo corrige por su cuenta**: lo reporta y el dueño de negocio decide.

## 10. Aprobadores

| Puerta | Rol | Nombre |
|---|---|---|
| Análisis | Líder solicitante | Gerente de Canales Digitales |
| Arquitectura | Arquitecto | Arquitecto de soluciones |
| Hallazgos de negocio | Dueño de negocio | Dueña del producto Transferencias |
| Seguridad y dinero | Riesgo / Seguridad | Oficial de riesgo tecnológico |
| Entrega a producción | Comité de cambios | Comité de cambios (CAB) |
