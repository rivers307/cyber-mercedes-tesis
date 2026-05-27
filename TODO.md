# TODO - Cobro por tiempo (estaciones)

- [x] 1) Leer y entender UI de estaciones (templates/JS)
- [x] 2) Extender `SesionPC` en `estaciones/models.py` con campos:
  - [x] tipo_cobro, duracion_programada_minutos, termina_en
  - [x] metodo_pago, cerrada_automaticamente
- [x] 3) Actualizar `estaciones/views.py` (inicio de sesión y cierre manual en `cambiar_estado`):
  - [x] recibir `tipo_cobro`, `duracion_programada_minutos` y `metodo_pago` por POST/JSON
  - [x] guardar esos campos en `SesionPC` y calcular cobro
- [ ] 4) Implementar cierre automático para sesiones con `tiempo_fijo`:
  - [ ] endpoint/API que cierre sesiones vencidas
  - [ ] integrarlo con polling desde `estaciones/templates/estaciones/dashboard.html`
- [x] 5) Refactor de cierre manual:
  - [x] calcular monto según `tipo_cobro`
  - [x] marcar `pagado`, guardar método y registrar `Ingreso` en `reportes/models.py`
- [x] 6) Actualizar `reportes/views.py` (`cierre_caja`) con desglose real por `metodo_pago`
- [x] 7) Migraciones y prueba manual
  - [x] `python manage.py makemigrations estaciones`
  - [x] `python manage.py migrate`

