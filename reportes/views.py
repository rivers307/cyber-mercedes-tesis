from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
from estaciones.models import Estacion
from sublimacion.models import Pedido, Producto
from inventario.models import MovimientoInventario, Insumo, ConciliacionInventario
from django.utils import timezone
from django.contrib import messages
import json

# ==================== VISTA PRINCIPAL ====================
@login_required
def dashboard_principal(request):
    from decimal import Decimal
    from reportes.models import Ingreso
    from estaciones.models import SesionPC
    from sublimacion.models import Pedido
    
    hoy = timezone.now().date()
    
    # Ingresos de hoy desde el modelo Ingreso
    ingresos_hoy = Ingreso.objects.filter(fecha__date=hoy).aggregate(total=Sum('monto'))['total'] or 0
    
    # Ingresos del mes
    ingresos_mes = Ingreso.objects.filter(fecha__month=hoy.month).aggregate(total=Sum('monto'))['total'] or 0
    
    # Sesiones de PCs de hoy (por hora_fin)
    sesiones_hoy = SesionPC.objects.filter(hora_fin__date=hoy, pagado=True).count()
    ingresos_pcs_hoy = SesionPC.objects.filter(hora_fin__date=hoy, pagado=True).aggregate(total=Sum('monto_cobrado'))['total'] or 0
    
    # ✅ CORREGIDO: tipo 'sublimacion_abono' en lugar de 'abono'
    abonos_hoy = Ingreso.objects.filter(fecha__date=hoy, tipo='sublimacion_abono').aggregate(total=Sum('monto'))['total'] or 0
    
    # Pedidos pendientes
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
    
    # Estadísticas de estaciones
    from estaciones.models import Estacion
    estaciones = Estacion.objects.all()
    total_estaciones = estaciones.count()
    estaciones_libres = estaciones.filter(estado='libre').count()
    estaciones_ocupadas = estaciones.filter(estado='ocupada').count()
    estaciones_mantenimiento = estaciones.filter(estado='mantenimiento').count()
    
    context = {
        # Totales de ingresos
        'ingresos_hoy': ingresos_hoy,
        'ingresos_mes': ingresos_mes,
        'ingresos_pcs_hoy': ingresos_pcs_hoy,
        'sesiones_hoy': sesiones_hoy,
        'abonos_hoy': abonos_hoy,
        'total_ingresos_hoy': float(ingresos_hoy) + float(ingresos_pcs_hoy),
        
        # Estadísticas de estaciones
        'total_estaciones': total_estaciones,
        'estaciones_libres': estaciones_libres,
        'estaciones_ocupadas': estaciones_ocupadas,
        'estaciones_mantenimiento': estaciones_mantenimiento,
        
        # Estadísticas de pedidos
        'pedidos_pendientes': pedidos_pendientes,
        
        # Usuario
        'usuario': request.user,
    }
    return render(request, 'reportes/dashboard_principal.html', context)
# ==================== REPORTE DE VENTAS ====================

@login_required
def ventas_view(request):
    """Reporte de ventas con gráficos"""
    # Usar “día local” para no depender de UTC
    hoy_local = timezone.localtime(timezone.now()).date()
    inicio_semana = hoy_local - timedelta(days=hoy_local.weekday())
    inicio_mes = hoy_local.replace(day=1)

    from reportes.models import Ingreso

    # Sublimación (Pedido)
    ingresos_hoy_pedidos = Pedido.objects.filter(
        fecha_pedido__gte=timezone.make_aware(datetime.combine(hoy_local, datetime.min.time()), timezone.get_current_timezone()),
        fecha_pedido__lt=timezone.make_aware(datetime.combine(hoy_local, datetime.max.time()), timezone.get_current_timezone()),
    ).aggregate(total=Sum('precio_total'))['total'] or 0

    ingresos_semana_pedidos = Pedido.objects.filter(
        fecha_pedido__date__gte=inicio_semana,
        fecha_pedido__date__lt=hoy_local + timedelta(days=1),
    ).aggregate(total=Sum('precio_total'))['total'] or 0

    ingresos_mes_pedidos = Pedido.objects.filter(
        fecha_pedido__date__gte=inicio_mes,
        fecha_pedido__date__lt=hoy_local + timedelta(days=1),
    ).aggregate(total=Sum('precio_total'))['total'] or 0

    abonos_pendientes = Pedido.objects.filter(abono__lt=F('precio_total')).aggregate(
        total=Sum(F('precio_total') - F('abono'))
    )['total'] or 0

    # PCs (Ingreso tipo='estacion')
    ingresos_hoy_pcs = Ingreso.objects.filter(
        fecha__gte=timezone.make_aware(datetime.combine(hoy_local, datetime.min.time()), timezone.get_current_timezone()),
        fecha__lt=timezone.make_aware(datetime.combine(hoy_local, datetime.max.time()), timezone.get_current_timezone()),
        tipo='estacion'
    ).aggregate(total=Sum('monto'))['total'] or 0

    ingresos_semana_pcs = Ingreso.objects.filter(
        fecha__date__gte=inicio_semana,
        fecha__date__lt=hoy_local + timedelta(days=1),
        tipo='estacion'
    ).aggregate(total=Sum('monto'))['total'] or 0

    ingresos_mes_pcs = Ingreso.objects.filter(
        fecha__date__gte=inicio_mes,
        fecha__date__lt=hoy_local + timedelta(days=1),
        tipo='estacion'
    ).aggregate(total=Sum('monto'))['total'] or 0

    ingresos_hoy = ingresos_hoy_pedidos + ingresos_hoy_pcs
    ingresos_semana = ingresos_semana_pedidos + ingresos_semana_pcs
    ingresos_mes = ingresos_mes_pedidos + ingresos_mes_pcs

    return render(request, 'reportes/ventas.html', {
        'ingresos_hoy': ingresos_hoy,
        'ingresos_semana': ingresos_semana,
        'ingresos_mes': ingresos_mes,
        'abonos_pendientes': abonos_pendientes,
    })

@login_required
def api_ventas_data(request):
    """API para datos de ventas (gráficos)"""
    periodo = request.GET.get('periodo', 'diario')
    hoy = timezone.now().date()
    
    if periodo == 'diario':
        fechas = [hoy - timedelta(days=i) for i in range(6, -1, -1)]
        ventas = []
        for fecha in fechas:
            total = Pedido.objects.filter(
                fecha_pedido__date=fecha
            ).aggregate(total=Sum('precio_total'))['total'] or 0
            ventas.append({
                'fecha': fecha.strftime('%d/%m'),
                'total': float(total)
            })

        # Sumamos ingresos de PCs desde Ingreso(tipo='estacion')
        from reportes.models import Ingreso
        for idx, f in enumerate(fechas):
            total_pcs = Ingreso.objects.filter(fecha__date=f, tipo='estacion').aggregate(total=Sum('monto'))['total'] or 0
            ventas[idx]['total'] = float(ventas[idx]['total']) + float(total_pcs)

        return JsonResponse({'ventas': ventas})
    
    elif periodo == 'semanal':
        ventas = []
        for i in range(11, -1, -1):
            inicio_semana = hoy - timedelta(weeks=i)
            fin_semana = inicio_semana + timedelta(days=6)
            total = Pedido.objects.filter(
                fecha_pedido__date__gte=inicio_semana,
                fecha_pedido__date__lte=fin_semana
            ).aggregate(total=Sum('precio_total'))['total'] or 0
            ventas.append(float(total))
        return JsonResponse({'ventas': ventas})
    
    else:  # mensual
        meses = []
        ventas = []
        for i in range(5, -1, -1):
            fecha = hoy.replace(day=1) - timedelta(days=30*i)
            total = Pedido.objects.filter(
                fecha_pedido__year=fecha.year,
                fecha_pedido__month=fecha.month
            ).aggregate(total=Sum('precio_total'))['total'] or 0
            meses.append(fecha.strftime('%B'))
            ventas.append(float(total))
        return JsonResponse({'ventas': ventas, 'meses': meses})

# ==================== REPORTE DE ESTACIONES ====================

@login_required
def estaciones_view(request):
    """Reporte de estaciones"""
    return render(request, 'reportes/estaciones.html')

@login_required
def api_estaciones_stats(request):
    """API para estadísticas de estaciones"""
    estaciones = Estacion.objects.all()
    stats = {
        'libres': estaciones.filter(estado='libre').count(),
        'ocupadas': estaciones.filter(estado='ocupada').count(),
        'mantenimiento': estaciones.filter(estado='mantenimiento').count(),
        'total': estaciones.count()
    }
    
    # Horas pico (simulado para el gráfico)
    horas_pico = []
    for hora in range(8, 22):
        horas_pico.append({
            'hora': f"{hora}:00",
            'uso': estaciones.filter(estado='ocupada').count() * ((hora - 7) / 10)
        })
    stats['horas_pico'] = horas_pico
    
    return JsonResponse(stats)

# ==================== REPORTE DE SUBLIMACIÓN ====================

@login_required
def sublimacion_view(request):
    """Reporte de sublimación"""
    return render(request, 'reportes/sublimacion.html')

@login_required
def api_sublimacion_stats(request):
    """API para estadísticas de sublimación"""
    estados = {}
    for estado, label in Pedido.ESTADOS:
        count = Pedido.objects.filter(estado=estado).count()
        estados[label] = count
    
    # Productos más vendidos
    productos = Producto.objects.annotate(
        total_vendidos=Sum('pedido__cantidad')
    ).filter(total_vendidos__gt=0).order_by('-total_vendidos')[:10]
    
    productos_data = []
    for p in productos:
        productos_data.append({
            'nombre': p.nombre,
            'total': p.total_vendidos or 0
        })
    
    return JsonResponse({
        'estados': estados,
        'productos': productos_data
    })

# ==================== REPORTE DE INVENTARIO ====================

@login_required
def inventario_view(request):
    """Reporte de inventario"""
    return render(request, 'reportes/inventario.html')

@login_required
def api_inventario_stats(request):
    """API para estadísticas de inventario"""
    insumos = Insumo.objects.all()
    total_valor = sum(i.stock_actual * float(i.precio_unitario) for i in insumos)
    stock_bajo = insumos.filter(stock_actual__lte=F('stock_minimo')).count()
    sin_stock = insumos.filter(stock_actual=0).count()
    
    # Movimientos recientes
    movimientos = MovimientoInventario.objects.all()[:20]
    movimientos_data = []
    for m in movimientos:
        movimientos_data.append({
            'fecha': m.fecha.strftime('%d/%m/%Y %H:%M'),
            'insumo': m.insumo.nombre,
            'tipo': m.get_tipo_display(),
            'cantidad': m.cantidad
        })
    
    return JsonResponse({
        'total_insumos': insumos.count(),
        'total_valor': float(total_valor),
        'stock_bajo': stock_bajo,
        'sin_stock': sin_stock,
        'movimientos': movimientos_data
    })

# ==================== CIERRE DE CAJA ====================

@login_required
def cierre_caja(request):
    """Cierre de caja diario"""
    from decimal import Decimal
    from reportes.models import Ingreso
    from estaciones.models import SesionPC
    
    hoy = timezone.now().date()
    
    # Obtener ingresos del día
    ingresos_dia = Ingreso.objects.filter(fecha__date=hoy)
    
    # Totales
    total_ventas = ingresos_dia.aggregate(total=Sum('monto'))['total'] or Decimal('0')
    total_abonos = ingresos_dia.filter(tipo='sublimacion_abono').aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    # Pendiente (por ahora en 0, puedes calcularlo después)
    total_pendiente = Decimal('0')
    
    # Pedidos entregados hoy
    from sublimacion.models import Pedido
    entregados_hoy = Pedido.objects.filter(
        estado='entregado', 
        fecha_entrega__date=hoy
    ).count()
    
    # Métodos de pago
    metodos_pago = {
        'efectivo': ingresos_dia.filter(metodo_pago='efectivo').aggregate(total=Sum('monto'))['total'] or Decimal('0'),
        'transferencia': ingresos_dia.filter(metodo_pago='transferencia').aggregate(total=Sum('monto'))['total'] or Decimal('0'),
        'pago_movil': ingresos_dia.filter(metodo_pago='pago_movil').aggregate(total=Sum('monto'))['total'] or Decimal('0'),
        'tarjeta': ingresos_dia.filter(metodo_pago='tarjeta').aggregate(total=Sum('monto'))['total'] or Decimal('0'),
    }
    
    # Ventas del día para la tabla
    ventas_dia = ingresos_dia.order_by('-fecha')
    
    if request.method == 'POST' and 'cerrar' in request.POST:
        return render(request, 'reportes/cierre_exitoso.html', {
            'fecha': hoy,
            'total_ventas': total_ventas,
            'total_abonos': total_abonos,
            'total_pendiente': total_pendiente,
        })
    
    return render(request, 'reportes/cierre_caja.html', {
        'fecha': hoy,
        'total_ventas': total_ventas,
        'total_abonos': total_abonos,
        'total_pendiente': total_pendiente,
        'entregados_hoy': entregados_hoy,
        'metodos_pago': metodos_pago,
        'ventas_dia': ventas_dia,
    })

# ==================== EXPORTAR REPORTES ====================

@login_required
def exportar_reporte(request, tipo):
    """Exportar reporte a CSV"""
    import csv
    from django.http import HttpResponse
    
    # Crear respuesta HTTP con cabeceras CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reporte_{tipo}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    if tipo == 'ventas':
        writer.writerow(['ID', 'Cliente', 'Producto', 'Cantidad', 'Total (Bs)', 'Estado', 'Fecha'])
        for p in Pedido.objects.all():
            writer.writerow([
                p.id, 
                p.nombre_cliente, 
                p.producto.nombre, 
                p.cantidad, 
                f"{p.precio_total:.2f}", 
                p.get_estado_display(), 
                p.fecha_pedido.strftime('%d/%m/%Y')
            ])
        return response
    
    elif tipo == 'pedidos':
        writer.writerow(['ID', 'Cliente', 'Producto', 'Estado', 'Abono (Bs)', 'Saldo (Bs)'])
        for p in Pedido.objects.all():
            writer.writerow([
                p.id, 
                p.nombre_cliente, 
                p.producto.nombre, 
                p.get_estado_display(), 
                f"{p.abono:.2f}", 
                f"{p.saldo_pendiente():.2f}"
            ])
        return response
    
    elif tipo == 'inventario':
        writer.writerow(['Código', 'Nombre', 'Categoría', 'Stock Actual', 'Stock Mínimo', 'Precio Unitario (Bs)', 'Valor Total (Bs)'])
        from inventario.models import Insumo
        for i in Insumo.objects.all():
            valor_total = i.stock_actual * float(i.precio_unitario)
            writer.writerow([
                i.codigo, 
                i.nombre, 
                i.categoria.nombre if i.categoria else 'Sin categoría', 
                i.stock_actual, 
                i.stock_minimo, 
                f"{float(i.precio_unitario):.2f}", 
                f"{valor_total:.2f}"
            ])
        return response
    
    elif tipo == 'insumos':
        writer.writerow(['ID', 'Nombre', 'Stock', 'Precio', 'Proveedor', 'Ubicación'])
        from inventario.models import Insumo
        for i in Insumo.objects.all():
            writer.writerow([
                i.id, 
                i.nombre, 
                i.stock_actual, 
                f"{float(i.precio_unitario):.2f}", 
                i.proveedor or '', 
                i.ubicacion or ''
            ])
        return response
    
    elif tipo == 'estaciones':
        writer.writerow(['Número', 'Estado', 'Precio por Hora (Bs)', 'Último Uso', 'Tiempo Acumulado (min)'])
        from estaciones.models import Estacion
        for e in Estacion.objects.all():
            writer.writerow([
                e.numero, 
                e.get_estado_display(), 
                f"{float(e.precio_hora):.2f}", 
                e.ultimo_uso.strftime('%d/%m/%Y %H:%M') if e.ultimo_uso else 'Nunca', 
                e.tiempo_acumulado
            ])
        return response
    
    else:
        # Si el tipo no es reconocido, redirigir al dashboard
        from django.shortcuts import redirect
        return redirect('dashboard')