from decimal import Decimal
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Estacion, SesionPC


@login_required
def dashboard_estaciones(request):
    """Vista principal del dashboard de estaciones"""
    estaciones = Estacion.objects.all().order_by('numero')

    tiempos = {}
    for estacion in estaciones:
        tiempos[estacion.id] = estacion.obtener_tiempo_actual()

    return render(request, 'estaciones/dashboard.html', {
        'estaciones': estaciones,
        'tiempos': tiempos,
    })


@login_required
def crear_estacion(request):
    """Crear una nueva estación (PC)"""
    if request.method == 'POST':
        numero = request.POST.get('numero')
        precio_hora = request.POST.get('precio_hora')
        estado = request.POST.get('estado', 'libre')

        if Estacion.objects.filter(numero=numero).exists():
            messages.error(request, f'La PC {numero} ya existe')
            return redirect('dashboard_estaciones')

        Estacion.objects.create(
            numero=numero,
            precio_hora=precio_hora,
            estado=estado,
        )
        messages.success(request, f'PC {numero} creada exitosamente')
        return redirect('dashboard_estaciones')

    return redirect('dashboard_estaciones')


@login_required
def editar_estacion(request, id):
    """Editar una estación existente"""
    estacion = get_object_or_404(Estacion, id=id)

    if request.method == 'POST':
        estacion.numero = request.POST.get('numero', estacion.numero)
        estacion.precio_hora = request.POST.get('precio_hora', estacion.precio_hora)
        estacion.estado = request.POST.get('estado', estacion.estado)
        estacion.save()
        messages.success(request, f'PC {estacion.numero} actualizada')
        return redirect('dashboard_estaciones')

    return redirect('dashboard_estaciones')


@login_required
def eliminar_estacion(request, id):
    """Eliminar una estación"""
    estacion = get_object_or_404(Estacion, id=id)
    numero = estacion.numero

    if request.method == 'POST':
        estacion.delete()
        messages.success(request, f'PC {numero} eliminada')
        return redirect('dashboard_estaciones')

    return redirect('dashboard_estaciones')


def _get_param(request, body: dict, key: str, default=None):
    if key in body:
        return body.get(key)
    return request.POST.get(key, default)


@csrf_exempt
@login_required
def cambiar_estado(request, id):
    """API para iniciar/finalizar uso de una estación con cobro (acumulado o tiempo fijo)."""
    from reportes.models import Ingreso

    if request.method != 'POST':
        return JsonResponse({'success': False})

    estacion = get_object_or_404(Estacion, id=id)

    # Acepta JSON o form-data
    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        body = {}

    tipo_cobro = _get_param(request, body, 'tipo_cobro', 'acumulado_horas')
    duracion_programada_minutos = _get_param(request, body, 'duracion_programada_minutos', None)

    if duracion_programada_minutos in ('', None):
        duracion_programada_minutos = None
    else:
        try:
            duracion_programada_minutos = int(duracion_programada_minutos)
        except Exception:
            duracion_programada_minutos = None

    metodo_pago = _get_param(request, body, 'metodo_pago', None)
    cliente_nombre = _get_param(request, body, 'cliente', f"Cliente_{estacion.numero}")

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

            # ✅ CORREGIDO: registrar ingreso correctamente
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


@csrf_exempt
@login_required
def cerrar_sesiones_vencidas(request):
    """Cierra automáticamente sesiones con `termina_en` vencido (tiempo fijo)."""
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

        # Cobro por tiempo fijo: cobrar por duración programada
        if sesion.duracion_programada_minutos:
            monto = (Decimal(sesion.duracion_programada_minutos) / 60) * estacion.precio_hora
        else:
            monto = (Decimal(tiempo_uso) / 60) * estacion.precio_hora

        sesion.monto_cobrado = monto
        sesion.pagado = True
        sesion.cerrada_automaticamente = True
        sesion.save()

        # ✅ CORREGIDO: registrar ingreso correctamente
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

        # Liberar estación
        estacion.estado = 'mantenimiento'
        estacion.hora_inicio = None
        estacion.save()

        cerradas += 1
        total_monto += monto

    return JsonResponse({'success': True, 'cerradas': cerradas, 'total_monto': str(total_monto)})


@login_required
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

