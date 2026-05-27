# TODO_AutoCierrePC

- [x] Actualizar modelo `reportes.models.Ingreso` para guardar `metodo_pago`.
- [x] Migrar cambios.
- [x] Actualizar `estaciones/views.py`:




  - [x] En finalización manual: incluir `metodo_pago` al crear `Ingreso`.
  - [x] En cierre automático `cerrar_sesiones_vencidas`: incluir `metodo_pago` al crear `Ingreso`.
- [ ] Actualizar `reportes/views.py`:
  - [x] `cierre_caja`: mantener desglose por `metodo_pago` usando `SesionPC` (ya que el ingreso se registra con el mismo método).
- [x] Extender `ventas_view` y `api_ventas_data` para incluir ingresos de PCs desde `Ingreso` (tipo='estacion') en el reporte de Ventas.
- [ ] Validar export CSV si aplica (opcional).

