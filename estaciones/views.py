from decimal import Decimal
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Estacion, SesionPC
from usuarios.decorators import empleado_required, admin_required
from reportes.utils import registrar_auditoria


# ============================================================
# ========== DASHBOARD ==========
# ============================================================
@empleado_required
def dashboard_estaciones(request):
    """Vista principal del dashboard de estaciones"""
    estaciones = Estacion.objects.all().order_by('numero')

    # Obtener sesiones activas
    sesiones_activas = SesionPC.objects.filter(
        pagado=False,
        hora_fin__isnull=True
    ).select_related('estacion')

    # Calcular tiempos y montos para cada sesión activa
    for sesion in sesiones_activas:
        sesion.tiempo_transcurrido = sesion.obtener_tiempo_transcurrido_formateado()
        sesion.monto_acumulado = sesion.calcular_monto_acumulado()

    # Calcular tiempos para estaciones ocupadas sin sesión (por si acaso)
    for estacion in estaciones:
        if estacion.estado == 'ocupada':
            # Verificar si tiene sesión activa
            tiene_sesion = any(s.estacion.id == estacion.id for s in sesiones_activas)
            if not tiene_sesion:
                # Si no tiene sesión activa, marcarla como libre (corrección automática)
                estacion.estado = 'libre'
                estacion.hora_inicio = None
                estacion.save()

    return render(request, 'estaciones/dashboard.html', {
        'estaciones': estaciones,
        'sesiones_activas': sesiones_activas,
    })


# ============================================================
# ========== CREAR ESTACIÓN (SOLO ADMIN) ==========
# ============================================================
@admin_required
@registrar_auditoria(
    accion='crear',
    modulo='Estaciones',
    obtener_descripcion=lambda r, **k: f"Creó PC {r.POST.get('numero', '')} - Precio: Bs {r.POST.get('precio_hora', '')}"
)
def crear_estacion(request):
    """Crear una nueva estación (PC)"""
    if request.method == 'POST':
        numero = request.POST.get('numero')
        precio_hora = request.POST.get('precio_hora')
        estado = request.POST.get('estado', 'libre')

        if Estacion.objects.filter(numero=numero).exists():
            messages.error(request, f'La PC {numero} ya existe')
            return redirect('estaciones:dashboard_estaciones')

        Estacion.objects.create(
            numero=numero,
            precio_hora=precio_hora,
            estado=estado,
        )
        messages.success(request, f'✅ PC {numero} creada exitosamente')
        return redirect('estaciones:dashboard_estaciones')

    return redirect('estaciones:dashboard_estaciones')


# ============================================================
# ========== EDITAR ESTACIÓN (SOLO ADMIN) ==========
# ============================================================
@admin_required
@registrar_auditoria(
    accion='editar',
    modulo='Estaciones',
    obtener_descripcion=lambda r, id, **k: f"Editó PC {r.POST.get('numero', '')} - Precio: Bs {r.POST.get('precio_hora', '')}"
)
def editar_estacion(request, id):
    """Editar una estación existente"""
    estacion = get_object_or_404(Estacion, id=id)

    if request.method == 'POST':
        estacion.numero = request.POST.get('numero', estacion.numero)
        estacion.precio_hora = request.POST.get('precio_hora', estacion.precio_hora)
        estacion.estado = request.POST.get('estado', estacion.estado)
        estacion.save()
        messages.success(request, f'✅ PC {estacion.numero} actualizada')
        return redirect('estaciones:dashboard_estaciones')

    return redirect('estaciones:dashboard_estaciones')


# ============================================================
# ========== ELIMINAR ESTACIÓN (SOLO ADMIN) ==========
# ============================================================
@admin_required
@registrar_auditoria(
    accion='eliminar',
    modulo='Estaciones',
    obtener_descripcion=lambda r, id, **k: f"Eliminó la PC N° {k.get('numero', '')}"
)
def eliminar_estacion(request, id):
    """Eliminar una estación (solo administradores)"""
    estacion = get_object_or_404(Estacion, id=id)
    numero = estacion.numero

    # Verificar si tiene sesiones activas
    sesion_activa = SesionPC.objects.filter(estacion=estacion, pagado=False, hora_fin__isnull=True).exists()

    if sesion_activa:
        messages.error(request, f'❌ No se puede eliminar la PC {numero} porque tiene una sesión activa')
        return redirect('estaciones:dashboard_estaciones')

    if request.method == 'POST':
        # Registrar en auditoría antes de eliminar
        registrar_auditoria(
            accion='eliminar',
            modulo='Estaciones',
            obtener_descripcion=lambda r, **k: f"Eliminó la PC N° {numero}"
        )(request)

        estacion.delete()
        messages.success(request, f'✅ PC {numero} eliminada exitosamente')
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# ============================================================
# ========== CAMBIAR ESTADO A MANTENIMIENTO (SOLO ADMIN) ==========
# ============================================================
@admin_required
@registrar_auditoria(
    accion='cambiar_estado',
    modulo='Estaciones',
    obtener_descripcion=lambda r, id, **k: f"Cambió PC {k.get('numero', '')} a estado {k.get('estado', '')}"
)
def cambiar_estado_mantenimiento(request, id):
    """Cambiar el estado de una PC a mantenimiento (solo admin)"""
    estacion = get_object_or_404(Estacion, id=id)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')

        if nuevo_estado not in ['libre', 'mantenimiento']:
            messages.error(request, 'Estado inválido')
            return JsonResponse({'success': False, 'error': 'Estado inválido'})

        if estacion.estado == 'ocupada' and nuevo_estado == 'mantenimiento':
            messages.error(request, f'❌ No se puede poner en mantenimiento una PC ocupada')
            return JsonResponse({'success': False, 'error': 'PC ocupada'})

        registrar_auditoria(
            accion='cambiar_estado',
            modulo='Estaciones',
            obtener_descripcion=lambda r, **k: f"Cambió PC {estacion.numero} de {estacion.estado} a {nuevo_estado}"
        )(request)

        estacion.estado = nuevo_estado
        if nuevo_estado == 'libre':
            estacion.hora_inicio = None
            estacion.tiempo_acumulado = 0
        estacion.save()

        messages.success(request, f'✅ PC {estacion.numero} cambiada a {nuevo_estado}')
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# ============================================================
# ========== INICIAR SESIÓN EN PC ==========
# ============================================================
@empleado_required
@registrar_auditoria(
    accion='iniciar_sesion',
    modulo='Estaciones',
    obtener_descripcion=lambda r, id, **k: f"Inició sesión en PC {k.get('numero', '')} - {k.get('tipo', '')}"
)
def iniciar_sesion(request, id):
    """Iniciar una sesión en una PC"""
    estacion = get_object_or_404(Estacion, id=id)

    if request.method != 'POST':
        return redirect('estaciones:dashboard_estaciones')

    if estacion.estado != 'libre':
        messages.error(request, f'❌ La PC {estacion.numero} no está disponible')
        return redirect('estaciones:dashboard_estaciones')

    tipo_cobro = request.POST.get('tipo_cobro')
    cliente_nombre = request.POST.get('cliente_nombre', f'Cliente_{estacion.numero}')
    metodo_pago = request.POST.get('metodo_pago')

    if tipo_cobro not in ['acumulado_horas', 'tiempo_fijo']:
        messages.error(request, 'Tipo de cobro inválido')
        return redirect('estaciones:dashboard_estaciones')

    if metodo_pago and metodo_pago not in ['efectivo', 'transferencia', 'pago_movil']:
        messages.error(request, 'Método de pago inválido')
        return redirect('estaciones:dashboard_estaciones')

    sesion = SesionPC(
        estacion=estacion,
        hora_inicio=timezone.now(),
        cliente_nombre=cliente_nombre,
        tipo_cobro=tipo_cobro,
        metodo_pago=metodo_pago,
    )

    if tipo_cobro == 'tiempo_fijo':
        duracion = request.POST.get('duracion_minutos')
        if duracion:
            try:
                duracion = int(duracion)
                if duracion > 0:
                    sesion.duracion_programada_minutos = duracion
                    sesion.termina_en = timezone.now() + timedelta(minutes=duracion)
            except ValueError:
                pass

    sesion.save()
    estacion.estado = 'ocupada'
    estacion.hora_inicio = timezone.now()
    estacion.tiempo_acumulado = 0
    estacion.save()

    messages.success(request, f'✅ Sesión iniciada en PC {estacion.numero}')
    return redirect('estaciones:dashboard_estaciones')


# ============================================================
# ========== OBTENER ESTADO DE SESIÓN (API) ==========
# ============================================================
@empleado_required
def obtener_estado_sesion(request, sesion_id):
    """API para obtener el estado actual de una sesión (para el contador)"""
    sesion = get_object_or_404(SesionPC, id=sesion_id)

    tiempo_transcurrido = sesion.obtener_tiempo_transcurrido()
    horas = tiempo_transcurrido // 60
    minutos = tiempo_transcurrido % 60

    data = {
        'id': sesion.id,
        'estacion': sesion.estacion.numero,
        'tipo': sesion.tipo_cobro,
        'cliente_nombre': sesion.cliente_nombre,
        'hora_inicio': sesion.hora_inicio.strftime('%H:%M:%S'),
        'tiempo_transcurrido': tiempo_transcurrido,
        'tiempo_formateado': f"{horas:02d}:{minutos:02d}:00",
        'tiempo_restante': sesion.obtener_tiempo_restante(),
        'monto_actual': float(sesion.calcular_monto_acumulado()),
        'precio_hora': float(sesion.estacion.precio_hora),
        'duracion_programada': sesion.duracion_programada_minutos,
    }

    return JsonResponse(data)


# ============================================================
# ========== FINALIZAR SESIÓN ==========
# ============================================================
@empleado_required
@registrar_auditoria(
    accion='finalizar_sesion',
    modulo='Estaciones',
    obtener_descripcion=lambda r, id, **k: f"Finalizó sesión PC {k.get('numero', '')} - Monto: Bs {k.get('monto', '')}"
)
def finalizar_sesion(request, sesion_id):
    """Finalizar una sesión y registrar el pago"""
    from reportes.models import Ingreso

    sesion = get_object_or_404(SesionPC, id=sesion_id)
    estacion = sesion.estacion

    if sesion.pagado:
        messages.warning(request, 'Esta sesión ya fue pagada')
        return redirect('estaciones:dashboard_estaciones')

    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago')
        monto_pagado = request.POST.get('monto_pagado')

        if not metodo_pago or metodo_pago not in ['efectivo', 'transferencia', 'pago_movil']:
            messages.error(request, 'Seleccione un método de pago válido')
            return redirect('estaciones:finalizar_sesion', sesion_id=sesion_id)

        monto = sesion.calcular_monto_acumulado()
        if monto_pagado:
            try:
                monto = Decimal(monto_pagado)
            except:
                pass

        sesion.hora_fin = timezone.now()
        sesion.tiempo_minutos = sesion.obtener_tiempo_transcurrido()
        sesion.monto_cobrado = monto
        sesion.pagado = True
        sesion.metodo_pago = metodo_pago
        sesion.save()

        Ingreso.objects.create(
            tipo='estacion',
            monto=monto,
            metodo_pago=metodo_pago,
            descripcion=f"PC {estacion.numero} - {sesion.get_tipo_cobro_display()} - {sesion.cliente_nombre}",
            sesion_relacionada=sesion,
            registrado_por=request.user,
        )

        estacion.estado = 'libre'
        estacion.hora_inicio = None
        estacion.tiempo_acumulado = 0
        estacion.save()

        messages.success(request, f'✅ Sesión finalizada. Total: Bs {monto:.2f}')
        return redirect('estaciones:dashboard_estaciones')

    context = {
        'sesion': sesion,
        'tiempo_total': sesion.obtener_tiempo_transcurrido_formateado(),
        'monto_total': sesion.calcular_monto_acumulado(),
    }
    return render(request, 'estaciones/finalizar_sesion.html', context)


# ============================================================
# ========== CAMBIAR ESTADO (API) - CON SOPORTE GET ==========
# ============================================================
@csrf_exempt
@empleado_required
@registrar_auditoria(
    accion='cambiar_estado',
    modulo='Estaciones',
    obtener_descripcion=lambda r, id, **k: f"Cambió estado de PC {id} - Acción: {r.POST.get('accion', 'desconocida')}"
)
def cambiar_estado(request, id):
    """API para obtener estado de sesión activa (GET) o iniciar/finalizar uso (POST)"""
    from reportes.models import Ingreso

    estacion = get_object_or_404(Estacion, id=id)

    # ============================================================
    # ===== MÉTODO GET: Devolver estado de sesión activa =====
    # ============================================================
    if request.method == 'GET':
        sesion_activa = SesionPC.objects.filter(
            estacion=estacion, 
            pagado=False, 
            hora_fin__isnull=True
        ).first()
        
        if sesion_activa:
            data = {
                'sesion_activa': True,
                'sesion_id': sesion_activa.id,
                'tiempo_transcurrido': sesion_activa.obtener_tiempo_transcurrido(),
                'tiempo_restante': sesion_activa.obtener_tiempo_restante(),
                'monto_actual': float(sesion_activa.calcular_monto_acumulado()),
                'cliente_nombre': sesion_activa.cliente_nombre,
                'tipo_cobro': sesion_activa.tipo_cobro,
            }
        else:
            data = {'sesion_activa': False}
        return JsonResponse(data)

    # ============================================================
    # ===== MÉTODO POST: Iniciar/Finalizar uso =====
    # ============================================================
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        body = {}

    tipo_cobro = body.get('tipo_cobro', 'acumulado_horas')
    duracion_programada_minutos = body.get('duracion_programada_minutos', None)
    metodo_pago = body.get('metodo_pago', None)
    cliente_nombre = body.get('cliente', f"Cliente_{estacion.numero}")

    if duracion_programada_minutos in ('', None):
        duracion_programada_minutos = None
    else:
        try:
            duracion_programada_minutos = int(duracion_programada_minutos)
        except Exception:
            duracion_programada_minutos = None

    now = timezone.now()

    # ========== INICIAR USO ==========
    if estacion.estado == 'libre':
        estacion.estado = 'ocupada'
        estacion.hora_inicio = now
        estacion.tiempo_acumulado = 0
        estacion.save()

        termina_en = None
        if tipo_cobro == 'tiempo_fijo' and duracion_programada_minutos:
            termina_en = now + timezone.timedelta(minutes=duracion_programada_minutos)

        SesionPC.objects.create(
            estacion=estacion,
            hora_inicio=now,
            cliente_nombre=cliente_nombre,
            tipo_cobro=tipo_cobro,
            duracion_programada_minutos=duracion_programada_minutos,
            termina_en=termina_en,
            metodo_pago=metodo_pago,
        )

        return JsonResponse({'success': True})

    # ========== FINALIZAR USO ==========
    if estacion.estado == 'ocupada':
        sesion = SesionPC.objects.filter(estacion=estacion, hora_fin__isnull=True).first()
        tiempo_uso = estacion.obtener_tiempo_actual()

        if sesion:
            sesion.hora_fin = now
            sesion.tiempo_minutos = tiempo_uso

            if sesion.tipo_cobro == 'tiempo_fijo' and sesion.duracion_programada_minutos:
                monto = (Decimal(sesion.duracion_programada_minutos) / 60) * estacion.precio_hora
            else:
                monto = (Decimal(tiempo_uso) / 60) * estacion.precio_hora

            sesion.monto_cobrado = monto
            sesion.pagado = True
            sesion.cerrada_automaticamente = False

            if not sesion.metodo_pago:
                sesion.metodo_pago = metodo_pago

            sesion.save()

            Ingreso.objects.create(
                tipo='estacion',
                monto=monto,
                metodo_pago=sesion.metodo_pago,
                descripcion=(
                    f"PC {estacion.numero} - {sesion.get_tipo_cobro_display()}"
                    f" - Cobro {'autom.' if sesion.cerrada_automaticamente else 'manual'}"
                ),
                sesion_relacionada=sesion,
                registrado_por=request.user,
            )

        estacion.estado = 'mantenimiento'
        estacion.hora_inicio = None
        estacion.save()

        messages.success(
            request,
            f'⏱️ PC {estacion.numero} - Tiempo: {tiempo_uso} min - Cobro aplicado.',
        )

        return JsonResponse({'success': True})

    # ========== MANTENIMIENTO ==========
    estacion.estado = 'libre'
    estacion.tiempo_acumulado = 0
    estacion.hora_inicio = None
    estacion.save()

    return JsonResponse({'success': True})


# ============================================================
# ========== CERRAR SESIONES VENCIDAS ==========
# ============================================================
@csrf_exempt
@empleado_required
def cerrar_sesiones_vencidas(request):
    """Cierra automáticamente sesiones con `termina_en` vencido (tiempo fijo)"""
    from reportes.models import Ingreso

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    now = timezone.now()

    vencidas = SesionPC.objects.filter(
        pagado=False,
        tipo_cobro='tiempo_fijo',
        termina_en__isnull=False,
        termina_en__lte=now,
        hora_fin__isnull=True,
    )

    cerradas = 0
    total_monto = Decimal('0')

    for sesion in vencidas.select_related('estacion'):
        estacion = sesion.estacion

        tiempo_uso = estacion.obtener_tiempo_actual()
        sesion.hora_fin = now
        sesion.tiempo_minutos = tiempo_uso

        if sesion.duracion_programada_minutos:
            monto = (Decimal(sesion.duracion_programada_minutos) / 60) * estacion.precio_hora
        else:
            monto = (Decimal(tiempo_uso) / 60) * estacion.precio_hora

        sesion.monto_cobrado = monto
        sesion.pagado = True
        sesion.cerrada_automaticamente = True
        sesion.save()

        Ingreso.objects.create(
            tipo='estacion',
            monto=monto,
            metodo_pago=sesion.metodo_pago,
            descripcion=(
                f"PC {estacion.numero} - {sesion.get_tipo_cobro_display()}"
                f" - Cobro autom."
            ),
            sesion_relacionada=sesion,
            registrado_por=request.user,
        )

        estacion.estado = 'mantenimiento'
        estacion.hora_inicio = None
        estacion.save()

        cerradas += 1
        total_monto += monto

    return JsonResponse({'success': True, 'cerradas': cerradas, 'total_monto': str(total_monto)})


# ============================================================
# ========== ESTADÍSTICAS API ==========
# ============================================================
@empleado_required
def estadisticas_api(request):
    """API para obtener estadísticas de estaciones"""
    estaciones = Estacion.objects.all()
    stats = {
        'libres': estaciones.filter(estado='libre').count(),
        'ocupadas': estaciones.filter(estado='ocupada').count(),
        'mantenimiento': estaciones.filter(estado='mantenimiento').count(),
        'total': estaciones.count(),
    }
    return JsonResponse(stats)