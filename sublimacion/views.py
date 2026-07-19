from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Producto, Pedido, HistorialEstado
from .forms import PedidoForm
from datetime import datetime
import json
from usuarios.decorators import empleado_required, admin_required
from reportes.utils import registrar_auditoria


# ========== LISTA DE PEDIDOS ==========
@empleado_required
def lista_pedidos(request):
    pedidos = Pedido.objects.all()
    return render(request, 'sublimacion/lista_pedidos.html', {
        'pedidos': pedidos,
        'section': 'lista'
    })


# ========== DASHBOARD ==========
@empleado_required
def dashboard_pedidos(request):
    pedidos_recientes = Pedido.objects.all().order_by('-fecha_pedido')[:10]
    estadisticas = {
        'pendientes': Pedido.objects.filter(estado='pendiente').count(),
        'diseño': Pedido.objects.filter(estado='diseño').count(),
        'produccion': Pedido.objects.filter(estado='produccion').count(),
        'listos': Pedido.objects.filter(estado='listo').count(),
        'entregados': Pedido.objects.filter(estado='entregado').count(),
    }
    productos = Producto.objects.all()
    pedido_actual = None
    pedido_id = request.GET.get('pedido')
    if pedido_id:
        pedido_actual = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'sublimacion/dashboard.html', {
        'pedidos_recientes': pedidos_recientes,
        'estadisticas': estadisticas,
        'productos': productos,
        'pedido_actual': pedido_actual,
    })


# ========== CREAR PEDIDO (EMPLEADO) ==========
@empleado_required
@registrar_auditoria(
    accion='crear',
    modulo='Sublimación - Pedidos',
    obtener_descripcion=lambda r, **k: f"Creó pedido - Cliente: {r.POST.get('nombre_cliente', '')} - Producto: {r.POST.get('producto', '')}"
)
def crear_pedido(request):
    if request.method == 'POST':
        form = PedidoForm(request.POST, request.FILES)
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.registrado_por = request.user
            
            producto = pedido.producto
            if producto.stock < pedido.cantidad:
                messages.error(request, f'Stock insuficiente. Solo hay {producto.stock} unidades')
                return render(request, 'sublimacion/crear_pedido.html', {'form': form, 'productos': Producto.objects.all()})
            
            # Calcular precio total usando precio_usd y tasa actual
            from reportes.models import TasaCambio
            tasa_obj = TasaCambio.objects.order_by('-fecha').first()
            tasa_valor = tasa_obj.tasa if tasa_obj else Decimal('60')
            
            pedido.precio_usd_unitario = producto.precio_usd
            pedido.tasa_usada = tasa_valor
            pedido.precio_total = producto.precio_usd * pedido.cantidad * tasa_valor
            
            pedido.save()
            producto.stock -= pedido.cantidad
            producto.save()
            
            if pedido.abono > 0:
                from reportes.models import Ingreso
                Ingreso.objects.create(
                    tipo='sublimacion_abono',
                    monto=pedido.abono,
                    descripcion=f'Abono inicial pedido #{pedido.id} - {pedido.nombre_cliente}',
                    registrado_por=request.user,
                    pedido_relacionado=pedido
                )
            
            messages.success(request, f'Pedido #{pedido.id} creado exitosamente')
            return redirect('detalle_pedido', pedido.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PedidoForm()
    
    productos = Producto.objects.all()
    return render(request, 'sublimacion/crear_pedido.html', {
        'form': form,
        'productos': productos,
        'section': 'crear'
    })


# ========== FORMULARIO DE CREACIÓN (GET) ==========
@empleado_required
def crear_pedido_form(request):
    storage = messages.get_messages(request)
    storage.used = True

    form = PedidoForm()
    productos = Producto.objects.all()
    return render(request, 'sublimacion/crear_pedido.html', {
        'form': form,
        'productos': productos,
        'section': 'crear'
    })


# ========== DETALLE DEL PEDIDO ==========
@empleado_required
def detalle_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    historial = pedido.historial.all()
    return render(request, 'sublimacion/detalle_pedido.html', {
        'pedido': pedido,
        'historial': historial,
        'saldo': pedido.saldo_pendiente()
    })


# ========== IMPRIMIR PEDIDO ==========
@empleado_required
def imprimir_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    return render(request, 'sublimacion/imprimir_pedido.html', {
        'pedido': pedido,
    })


# ========== CAMBIAR ESTADO ==========
@csrf_exempt
@empleado_required
@registrar_auditoria(
    accion='cambiar_estado',
    modulo='Sublimación - Pedidos',
    obtener_descripcion=lambda r, id, **k: f"Cambió estado del pedido #{id} a {r.POST.get('estado', '')}"
)
def cambiar_estado(request, id):
    from decimal import Decimal
    from reportes.models import Ingreso
    from django.utils import timezone
    
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=id)
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado and nuevo_estado != pedido.estado:
            estado_anterior = pedido.estado
            
            HistorialEstado.objects.create(
                pedido=pedido,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado,
                cambiado_por=request.user
            )
            
            pedido.estado = nuevo_estado
            
            if nuevo_estado == 'entregado' and estado_anterior != 'entregado':
                pedido.fecha_entrega = timezone.now()
                saldo_restante = pedido.saldo_pendiente()
                
                if saldo_restante > 0:
                    Ingreso.objects.create(
                        tipo='sublimacion_pedido',
                        monto=saldo_restante,
                        descripcion=f'Pago final pedido #{pedido.id} - {pedido.nombre_cliente} - {pedido.producto.nombre}',
                        registrado_por=request.user,
                        pedido_relacionado=pedido
                    )
            
            pedido.save()
            messages.success(request, f'Estado actualizado a {pedido.get_estado_display()}')
        
        return redirect('detalle_pedido', pedido.id)
    
    return redirect('detalle_pedido', id)


# ========== REGISTRAR ABONO ==========
@empleado_required
@registrar_auditoria(
    accion='abono',
    modulo='Sublimación - Pagos',
    obtener_descripcion=lambda r, id, **k: f"Registró abono de Bs {r.POST.get('monto', 0)} al pedido #{id}"
)
def registrar_abono(request, id):
    from decimal import Decimal
    from reportes.models import Ingreso
    
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=id)
        
        try:
            monto = Decimal(str(request.POST.get('monto', 0)))
            
            if monto > 0 and monto <= pedido.saldo_pendiente():
                pedido.abono += monto
                pedido.save()
                
                Ingreso.objects.create(
                    tipo='sublimacion_abono',
                    monto=monto,
                    descripcion=f'Abono al pedido #{pedido.id} - {pedido.nombre_cliente}',
                    registrado_por=request.user,
                    pedido_relacionado=pedido
                )
                
                messages.success(request, f'✅ Abono de Bs {monto:.2f} registrado. Saldo pendiente: Bs {pedido.saldo_pendiente():.2f}')
            else:
                messages.error(request, 'Monto inválido o mayor al saldo pendiente')
        except (ValueError, TypeError):
            messages.error(request, 'Monto inválido')
        
        return redirect('detalle_pedido', pedido.id)
    
    return redirect('detalle_pedido', id)


# ========== GESTIÓN DE PRODUCTOS ==========
@admin_required
@registrar_auditoria(
    accion='crear',
    modulo='Sublimación - Productos',
    obtener_descripcion=lambda r, **k: f"Creó producto {r.POST.get('nombre', '')} - Tipo: {r.POST.get('tipo', '')} - USD: {r.POST.get('precio_usd', '')}"
)
def gestionar_productos(request):
    productos = Producto.objects.all()
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        tipo = request.POST.get('tipo')
        precio_usd = request.POST.get('precio_usd')
        stock = request.POST.get('stock', 0)
        stock_minimo = request.POST.get('stock_minimo', 5)
        
        # Convertir a Decimal
        try:
            precio_usd = Decimal(precio_usd.replace(',', '.'))
        except:
            precio_usd = Decimal('0')
        
        Producto.objects.create(
            nombre=nombre,
            tipo=tipo,
            precio_usd=precio_usd,
            stock=stock,
            stock_minimo=stock_minimo
        )
        messages.success(request, 'Producto agregado exitosamente')
        return redirect('gestionar_productos')
    
    return render(request, 'sublimacion/productos.html', {
        'productos': productos,
        'section': 'productos'
    })


# ========== EDITAR PRODUCTO ==========
@admin_required
@registrar_auditoria(
    accion='editar',
    modulo='Sublimación - Productos',
    obtener_descripcion=lambda r, id, **k: f"Editó producto #{id} - {r.POST.get('nombre', '')} - USD: {r.POST.get('precio_usd', '')}"
)
def editar_producto(request, id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=id)
        producto.nombre = request.POST.get('nombre')
        producto.tipo = request.POST.get('tipo')
        precio_usd = request.POST.get('precio_usd')
        
        try:
            producto.precio_usd = Decimal(precio_usd.replace(',', '.'))
        except:
            producto.precio_usd = Decimal('0')
        
        producto.stock = request.POST.get('stock')
        producto.stock_minimo = request.POST.get('stock_minimo')
        producto.save()
        messages.success(request, 'Producto actualizado')
        return redirect('gestionar_productos')
    
    return redirect('gestionar_productos')


# ========== ELIMINAR PRODUCTO ==========
@admin_required
@registrar_auditoria(
    accion='eliminar',
    modulo='Sublimación - Productos',
    obtener_descripcion=lambda r, id, **k: f"Eliminó producto #{id} - {r.POST.get('nombre', '')}"
)
def eliminar_producto(request, id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=id)
        producto.delete()
        messages.success(request, 'Producto eliminado')
        return redirect('gestionar_productos')
    
    return redirect('gestionar_productos')


# ========== ELIMINAR PEDIDO ==========
@admin_required
@registrar_auditoria(
    accion='eliminar',
    modulo='Sublimación - Pedidos',
    obtener_descripcion=lambda r, id, **k: f"Eliminó pedido #{id} - Motivo: {r.POST.get('motivo', 'No especificado')}"
)
def eliminar_pedido(request, id):
    from inventario.models import Auditoria
    
    if request.method != 'POST':
        return redirect('lista_pedidos')
    
    pedido = get_object_or_404(Pedido, id=id)
    
    password = request.POST.get('password')
    motivo = request.POST.get('motivo', '')
    
    if not request.user.check_password(password):
        messages.error(request, '❌ Contraseña incorrecta. No se pudo eliminar el pedido.')
        return redirect('lista_pedidos')
    
    if not motivo:
        messages.error(request, '❌ Debes especificar un motivo para eliminar el pedido.')
        return redirect('lista_pedidos')
    
    datos_pedido = {
        'id': pedido.id,
        'cliente': pedido.nombre_cliente,
        'producto': pedido.producto.nombre,
        'cantidad': pedido.cantidad,
        'total': str(pedido.precio_total),
        'estado': pedido.estado,
        'fecha': pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M')
    }
    
    pedido.delete()
    
    Auditoria.objects.create(
        usuario=request.user,
        accion='eliminar',
        modulo='Sublimación - Pedidos',
        descripcion=f'Eliminó el pedido #{datos_pedido["id"]} - Cliente: {datos_pedido["cliente"]} - Producto: {datos_pedido["producto"]} - Motivo: {motivo}',
        ip_origen=request.META.get('REMOTE_ADDR', 'Local'),
        registro_id=datos_pedido["id"],
        registro_nombre=f'Pedido #{datos_pedido["id"]} - {datos_pedido["cliente"]}'
    )
    
    messages.success(request, f'✅ Pedido #{datos_pedido["id"]} eliminado correctamente.')
    return redirect('lista_pedidos')


# ========== NOTAS TÉCNICAS ==========
@empleado_required
def guardar_notas_produccion(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    if request.method == 'POST':
        notas = request.POST.get('notas_produccion', '')
        pedido.notas_produccion = notas
        pedido.save()
        messages.success(request, "Notas de producción guardadas correctamente.")
    return redirect('detalle_pedido', id=pedido.id)


# ============================================================
# ===== VISTAS PARA CLIENTES =====
# ============================================================

@login_required
def productos_cliente(request):
    """Lista de productos disponibles para clientes"""
    from reportes.models import TasaCambio
    productos = Producto.objects.filter(stock__gt=0).order_by('tipo', 'nombre')
    tasa_obj = TasaCambio.objects.order_by('-fecha').first()
    return render(request, 'sublimacion/productos_cliente.html', {
        'productos': productos,
        'tasa': tasa_obj.tasa if tasa_obj else 60,
    })

@login_required
def crear_pedido_cliente(request):
    from reportes.models import TasaCambio
    
    # Obtener la tasa más reciente
    tasa_obj = TasaCambio.objects.order_by('-fecha').first()
    tasa_actual = tasa_obj.tasa if tasa_obj else Decimal('60')
    
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        cantidad = int(request.POST.get('cantidad', 1))
        especificaciones = request.POST.get('especificaciones', '')
        direccion_cliente = request.POST.get('direccion_cliente', '')
        telefono_cliente = request.POST.get('telefono_cliente', '')
        
        producto = get_object_or_404(Producto, id=producto_id)
        if producto.stock < cantidad:
            messages.error(request, 'No hay suficiente stock disponible.')
            return redirect('sublimacion:productos_cliente')
        
        # Calcular precio total en Bs según tasa actual
        precio_bs = producto.precio_usd * tasa_actual
        precio_total = precio_bs * cantidad
        
        from django.db import transaction
        with transaction.atomic():
            pedido = Pedido.objects.create(
                producto=producto,
                cantidad=cantidad,
                especificaciones=especificaciones,
                nombre_cliente=request.user.get_full_name() or request.user.username,
                telefono_cliente=telefono_cliente,
                direccion_cliente=direccion_cliente,
                precio_total=precio_total,
                precio_usd_unitario=producto.precio_usd,
                tasa_usada=tasa_actual,
                registrado_por=request.user,
                cliente=request.user,
                estado='pendiente'
            )
            producto.stock -= cantidad
            producto.save()
            
            messages.success(request, f'✅ Pedido #{pedido.id} creado exitosamente. Espera confirmación.')
            return redirect('sublimacion:mis_pedidos')
    
    # GET: mostrar formulario
    producto_id = request.GET.get('producto_id')
    producto = None
    if producto_id:
        producto = get_object_or_404(Producto, id=producto_id)
    productos = Producto.objects.filter(stock__gt=0).order_by('tipo', 'nombre')
    
    return render(request, 'sublimacion/crear_pedido_cliente.html', {
        'producto': producto,
        'productos': productos,
        'tasa': tasa_actual,
        'tasa_obj': tasa_obj,
    })

@login_required
def mis_pedidos(request):
    """Lista de pedidos del cliente autenticado"""
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-fecha_pedido')
    return render(request, 'sublimacion/mis_pedidos.html', {'pedidos': pedidos})

@login_required
def tabulador_precios_cliente(request):
    """Tabulador de precios para clientes con tasa de cambio actual"""
    from reportes.models import TasaCambio
    productos = Producto.objects.filter(stock__gt=0).order_by('tipo', 'nombre')
    tasa_obj = TasaCambio.objects.order_by('-fecha').first()
    return render(request, 'sublimacion/tabulador_precios_cliente.html', {
        'productos': productos,
        'tasa': tasa_obj.tasa if tasa_obj else 60,
    })