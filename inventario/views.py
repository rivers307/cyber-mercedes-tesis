from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from .models import (
    Insumo, Categoria, MovimientoInventario, AlertaStock,
    ActivoFijo, AuditoriaProgramada, InventarioTeorico, 
    HallazgoAuditoria, ConciliacionInventario
)
from sublimacion.models import Pedido
import json

# ========== VISTAS EXISTENTES (Dashboard, Lista, etc.) ==========

@login_required
def dashboard_inventario(request):
    """Dashboard principal del inventario"""
    insumos = Insumo.objects.all()
    activos = ActivoFijo.objects.all()
    
    # Estadísticas de insumos
    total_insumos = insumos.count()
    stock_bajo = insumos.filter(stock_actual__lte=models.F('stock_minimo')).count()
    sin_stock = insumos.filter(stock_actual=0).count()
    valor_total = sum(insumo.stock_actual * float(insumo.precio_unitario) for insumo in insumos)
    
    # Estadísticas de activos fijos
    total_activos = activos.count()
    activos_operativos = activos.filter(estado='operativo').count()
    activos_danados = activos.filter(estado='dañado').count()
    
    porcentaje_operatividad = (activos_operativos / total_activos * 100) if total_activos > 0 else 0
    
    # Alertas no leídas
    alertas = AlertaStock.objects.filter(leida=False)[:10]
    
    # Últimos movimientos
    ultimos_movimientos = MovimientoInventario.objects.all()[:15]
    
    # Auditorías activas
    auditorias_activas = AuditoriaProgramada.objects.filter(activa=True).count()
    
    context = {
        'total_insumos': total_insumos,
        'stock_bajo': stock_bajo,
        'sin_stock': sin_stock,
        'valor_total': valor_total,
        'alertas': alertas,
        'ultimos_movimientos': ultimos_movimientos,
        'insumos': insumos,
        'total_activos': total_activos,
        'activos_operativos': activos_operativos,
        'activos_danados': activos_danados,
        'porcentaje_operatividad': porcentaje_operatividad,
        'auditorias_activas': auditorias_activas,
    }
    return render(request, 'inventario/dashboard.html', context)

@login_required
def lista_insumos(request):
    """Lista de todos los insumos"""
    insumos = Insumo.objects.all()
    categorias = Categoria.objects.all()
    return render(request, 'inventario/lista_insumos.html', {
        'insumos': insumos,
        'categorias': categorias
    })

@login_required
def registrar_entrada(request):
    """Registrar entrada de insumos (compra)"""
    if request.method == 'POST':
        insumo_id = request.POST.get('insumo')
        cantidad = int(request.POST.get('cantidad'))
        motivo = request.POST.get('motivo', 'Compra de insumos')
        
        insumo = get_object_or_404(Insumo, id=insumo_id)
        stock_anterior = insumo.stock_actual
        stock_nuevo = stock_anterior + cantidad
        
        # Crear movimiento
        MovimientoInventario.objects.create(
            insumo=insumo,
            tipo='entrada',
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            motivo=motivo,
            realizado_por=request.user
        )
        
        # Actualizar stock
        insumo.stock_actual = stock_nuevo
        insumo.save()
        
        messages.success(request, f'Se registró entrada de {cantidad} {insumo.unidad} de {insumo.nombre}')
        return redirect('lista_insumos')
    
    insumos = Insumo.objects.all()
    return render(request, 'inventario/registrar_entrada.html', {'insumos': insumos})

@login_required
def registrar_salida(request):
    """Registrar salida de insumos (uso)"""
    if request.method == 'POST':
        insumo_id = request.POST.get('insumo')
        cantidad = int(request.POST.get('cantidad'))
        motivo = request.POST.get('motivo', 'Uso en producción')
        pedido_id = request.POST.get('pedido_relacionado')
        
        insumo = get_object_or_404(Insumo, id=insumo_id)
        
        # Verificar stock suficiente
        if insumo.stock_actual < cantidad:
            messages.error(request, f'Stock insuficiente. Solo hay {insumo.stock_actual} {insumo.unidad}')
            return redirect('registrar_salida')
        
        stock_anterior = insumo.stock_actual
        stock_nuevo = stock_anterior - cantidad
        
        # Crear movimiento
        movimiento = MovimientoInventario.objects.create(
            insumo=insumo,
            tipo='salida',
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            motivo=motivo,
            realizado_por=request.user
        )
        
        # Si está relacionado con un pedido
        if pedido_id:
            pedido = get_object_or_404(Pedido, id=pedido_id)
            movimiento.pedido_relacionado = pedido
            movimiento.save()
        
        # Actualizar stock
        insumo.stock_actual = stock_nuevo
        insumo.save()
        
        # Verificar si genera alerta
        if insumo.stock_actual <= insumo.stock_minimo:
            AlertaStock.objects.create(
                insumo=insumo,
                stock_actual=insumo.stock_actual,
                stock_minimo=insumo.stock_minimo
            )
            messages.warning(request, f'⚠️ Alerta: {insumo.nombre} está en stock mínimo')
        
        messages.success(request, f'Se registró salida de {cantidad} {insumo.unidad} de {insumo.nombre}')
        return redirect('lista_insumos')
    
    insumos = Insumo.objects.all()
    pedidos = Pedido.objects.filter(estado__in=['produccion', 'diseño'])[:20]
    return render(request, 'inventario/registrar_salida.html', {
        'insumos': insumos,
        'pedidos': pedidos
    })

@login_required
def crear_insumo(request):
    """Crear nuevo insumo"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        categoria_id = request.POST.get('categoria')
        unidad = request.POST.get('unidad')
        stock_actual = int(request.POST.get('stock_actual', 0))
        stock_minimo = int(request.POST.get('stock_minimo', 5))
        precio_unitario = request.POST.get('precio_unitario', 0)
        proveedor = request.POST.get('proveedor', '')
        ubicacion = request.POST.get('ubicacion', '')
        
        insumo = Insumo.objects.create(
            nombre=nombre,
            categoria_id=categoria_id if categoria_id else None,
            unidad=unidad,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            precio_unitario=precio_unitario,
            proveedor=proveedor,
            ubicacion=ubicacion
        )
        
        # Generar código automático
        insumo.codigo = f"INS-{insumo.id:04d}"
        insumo.save()
        
        messages.success(request, f'Insumo {nombre} creado exitosamente')
        return redirect('lista_insumos')
    
    categorias = Categoria.objects.all()
    return render(request, 'inventario/crear_insumo.html', {'categorias': categorias})

@login_required
def editar_insumo(request, id):
    """Editar insumo"""
    insumo = get_object_or_404(Insumo, id=id)
    
    if request.method == 'POST':
        insumo.nombre = request.POST.get('nombre')
        insumo.categoria_id = request.POST.get('categoria')
        insumo.unidad = request.POST.get('unidad')
        insumo.stock_minimo = int(request.POST.get('stock_minimo', 5))
        insumo.precio_unitario = request.POST.get('precio_unitario', 0)
        insumo.proveedor = request.POST.get('proveedor', '')
        insumo.ubicacion = request.POST.get('ubicacion', '')
        insumo.notas = request.POST.get('notas', '')
        insumo.save()
        
        messages.success(request, f'Insumo {insumo.nombre} actualizado')
        return redirect('lista_insumos')
    
    categorias = Categoria.objects.all()
    return render(request, 'inventario/editar_insumo.html', {
        'insumo': insumo,
        'categorias': categorias
    })

@login_required
def eliminar_insumo(request, id):
    """Eliminar insumo"""
    if request.method == 'POST':
        insumo = get_object_or_404(Insumo, id=id)
        nombre = insumo.nombre
        insumo.delete()
        messages.success(request, f'Insumo {nombre} eliminado')
        return redirect('lista_insumos')
    return redirect('lista_insumos')

@login_required
def historial_movimientos(request):
    """Ver historial completo de movimientos (auditoría)"""
    movimientos = MovimientoInventario.objects.all()
    
    # Filtros
    tipo = request.GET.get('tipo')
    insumo_id = request.GET.get('insumo')
    
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    if insumo_id:
        movimientos = movimientos.filter(insumo_id=insumo_id)
    
    return render(request, 'inventario/historial.html', {
        'movimientos': movimientos,
        'insumos': Insumo.objects.all(),
        'tipos': MovimientoInventario.TIPOS_MOVIMIENTO
    })

@login_required
@csrf_exempt
def marcar_alerta_leida(request, id):
    """Marcar alerta como leída"""
    if request.method == 'POST':
        alerta = get_object_or_404(AlertaStock, id=id)
        alerta.leida = True
        alerta.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def crear_categoria(request):
    """Crear nueva categoría"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        Categoria.objects.create(nombre=nombre, descripcion=descripcion)
        messages.success(request, f'Categoría {nombre} creada')
        return redirect('lista_insumos')
    return redirect('lista_insumos')

# ========== NUEVAS VISTAS PARA AUDITORÍA COMUNAL ==========

@login_required
def gestion_activos(request):
    """Gestión de activos fijos"""
    activos = ActivoFijo.objects.all()
    
    # Estadísticas de operatividad
    total = activos.count()
    operativos = activos.filter(estado='operativo').count()
    parciales = activos.filter(estado='parcial').count()
    danados = activos.filter(estado='dañado').count()
    obsoletos = activos.filter(estado='obsoleto').count()
    
    porcentaje_operatividad = (operativos / total * 100) if total > 0 else 0
    
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        nombre = request.POST.get('nombre')
        tipo = request.POST.get('tipo')
        estado = request.POST.get('estado')
        ubicacion = request.POST.get('ubicacion')
        marca = request.POST.get('marca', '')
        modelo = request.POST.get('modelo', '')
        valor_inicial = request.POST.get('valor_inicial', 0)
        fecha_adquisicion = request.POST.get('fecha_adquisicion') or None
        
        ActivoFijo.objects.create(
            codigo=codigo,
            nombre=nombre,
            tipo=tipo,
            estado=estado,
            ubicacion=ubicacion,
            marca=marca,
            modelo=modelo,
            valor_inicial=valor_inicial,
            fecha_adquisicion=fecha_adquisicion
        )
        messages.success(request, f'Activo {nombre} registrado')
        return redirect('gestion_activos')
    
    return render(request, 'inventario/activos.html', {
        'activos': activos,
        'total': total,
        'operativos': operativos,
        'parciales': parciales,
        'danados': danados,
        'obsoletos': obsoletos,
        'porcentaje_operatividad': porcentaje_operatividad
    })

@login_required
def programar_auditoria(request):
    """Programar una nueva auditoría"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        tipo = request.POST.get('tipo')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        
        auditoria = AuditoriaProgramada.objects.create(
            nombre=nombre,
            tipo=tipo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activa=True
        )
        
        # Generar inventario teórico automático
        for insumo in Insumo.objects.all():
            InventarioTeorico.objects.create(
                auditoria=auditoria,
                insumo=insumo,
                cantidad_teorica=insumo.stock_actual
            )
        
        for activo in ActivoFijo.objects.all():
            InventarioTeorico.objects.create(
                auditoria=auditoria,
                activo=activo,
                estado_teorico=activo.estado
            )
        
        messages.success(request, f'Auditoría "{nombre}" programada exitosamente')
        return redirect('lista_auditorias')
    
    return render(request, 'inventario/programar_auditoria.html')

@login_required
def lista_auditorias(request):
    """Lista de auditorías programadas"""
    auditorias = AuditoriaProgramada.objects.all().order_by('-fecha_inicio')
    return render(request, 'inventario/lista_auditorias.html', {'auditorias': auditorias})

@login_required
def realizar_auditoria(request, id):
    """Realizar auditoría física (ingresar hallazgos)"""
    auditoria = get_object_or_404(AuditoriaProgramada, id=id)
    inventario_teorico = InventarioTeorico.objects.filter(auditoria=auditoria)
    
    if request.method == 'POST':
        # Procesar hallazgos de insumos
        for item in inventario_teorico.filter(insumo__isnull=False):
            cantidad_fisica = request.POST.get(f'cantidad_fisica_{item.id}')
            if cantidad_fisica:
                HallazgoAuditoria.objects.create(
                    auditoria=auditoria,
                    insumo=item.insumo,
                    cantidad_fisica=int(cantidad_fisica),
                    observaciones=request.POST.get(f'obs_{item.id}', ''),
                    registrado_por=request.user
                )
        
        # Procesar hallazgos de activos
        for item in inventario_teorico.filter(activo__isnull=False):
            estado_fisico = request.POST.get(f'estado_fisico_{item.id}')
            if estado_fisico:
                HallazgoAuditoria.objects.create(
                    auditoria=auditoria,
                    activo=item.activo,
                    estado_fisico=estado_fisico,
                    observaciones=request.POST.get(f'obs_{item.id}', ''),
                    registrado_por=request.user
                )
        
        messages.success(request, 'Hallazgos registrados. Ahora puede proceder a la conciliación.')
        return redirect('conciliar_auditoria', auditoria.id)
    
    return render(request, 'inventario/realizar_auditoria.html', {
        'auditoria': auditoria,
        'inventario_teorico': inventario_teorico
    })

@login_required
def conciliar_auditoria(request, id):
    """Conciliar diferencias entre teórico y físico"""
    auditoria = get_object_or_404(AuditoriaProgramada, id=id)
    hallazgos = HallazgoAuditoria.objects.filter(auditoria=auditoria)
    
    if request.method == 'POST':
        for hallazgo in hallazgos:
            if hallazgo.insumo:
                # Buscar teórico
                teorico = InventarioTeorico.objects.get(auditoria=auditoria, insumo=hallazgo.insumo)
                variacion = teorico.cantidad_teorica - hallazgo.cantidad_fisica
                
                justificacion = request.POST.get(f'justificacion_{hallazgo.id}')
                detalle = request.POST.get(f'detalle_{hallazgo.id}', '')
                costo = request.POST.get(f'costo_{hallazgo.id}', 0)
                
                if variacion != 0:
                    ConciliacionInventario.objects.create(
                        auditoria=auditoria,
                        insumo=hallazgo.insumo,
                        cantidad_teorica=teorico.cantidad_teorica,
                        cantidad_fisica=hallazgo.cantidad_fisica,
                        variacion=variacion,
                        justificacion=justificacion,
                        detalle_justificacion=detalle,
                        costo_reposicion=costo,
                        conciliado_por=request.user
                    )
            
            elif hallazgo.activo:
                teorico = InventarioTeorico.objects.get(auditoria=auditoria, activo=hallazgo.activo)
                
                justificacion = request.POST.get(f'justificacion_{hallazgo.id}')
                detalle = request.POST.get(f'detalle_{hallazgo.id}', '')
                
                if teorico.estado_teorico != hallazgo.estado_fisico:
                    ConciliacionInventario.objects.create(
                        auditoria=auditoria,
                        activo=hallazgo.activo,
                        estado_teorico=teorico.estado_teorico,
                        estado_fisico=hallazgo.estado_fisico,
                        justificacion=justificacion,
                        detalle_justificacion=detalle,
                        conciliado_por=request.user
                    )
        
        auditoria.activa = False
        auditoria.save()
        messages.success(request, 'Auditoría conciliada exitosamente')
        return redirect('reporte_auditoria', auditoria.id)
    
    # Preparar datos para conciliación
    items_conciliacion = []
    for hallazgo in hallazgos:
        if hallazgo.insumo:
            teorico = InventarioTeorico.objects.get(auditoria=auditoria, insumo=hallazgo.insumo)
            items_conciliacion.append({
                'hallazgo': hallazgo,
                'teorico': teorico.cantidad_teorica,
                'variacion': teorico.cantidad_teorica - hallazgo.cantidad_fisica,
                'tipo': 'insumo'
            })
        else:
            teorico = InventarioTeorico.objects.get(auditoria=auditoria, activo=hallazgo.activo)
            items_conciliacion.append({
                'hallazgo': hallazgo,
                'teorico': teorico.estado_teorico,
                'tipo': 'activo'
            })
    
    return render(request, 'inventario/conciliar_auditoria.html', {
        'auditoria': auditoria,
        'items': items_conciliacion,
        'justificaciones': ConciliacionInventario.JUSTIFICACIONES
    })

@login_required
def reporte_auditoria(request, id):
    """Generar reporte completo de auditoría"""
    auditoria = get_object_or_404(AuditoriaProgramada, id=id)
    conciliaciones = ConciliacionInventario.objects.filter(auditoria=auditoria)
    
    # Calcular costo total de reposición
    costo_total_reposicion = sum(float(c.costo_reposicion) for c in conciliaciones)
    
    # Resumen por tipo de justificación
    resumen_justificaciones = {}
    for justif in dict(ConciliacionInventario.JUSTIFICACIONES).keys():
        count = conciliaciones.filter(justificacion=justif).count()
        if count > 0:
            resumen_justificaciones[justif] = count
    
    return render(request, 'inventario/reporte_auditoria.html', {
        'auditoria': auditoria,
        'conciliaciones': conciliaciones,
        'costo_total_reposicion': costo_total_reposicion,
        'resumen_justificaciones': resumen_justificaciones
    })