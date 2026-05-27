from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Producto, Pedido, HistorialEstado
from datetime import datetime
import json

@login_required
def lista_pedidos(request):
    """Lista todos los pedidos"""
    pedidos = Pedido.objects.all()
    return render(request, 'sublimacion/lista_pedidos.html', {
        'pedidos': pedidos,
        'section': 'lista'
    })

@login_required
def dashboard_pedidos(request):
    """Dashboard principal de sublimación"""
    pedidos_recientes = Pedido.objects.all()[:10]
    estadisticas = {
        'pendientes': Pedido.objects.filter(estado='pendiente').count(),
        'diseño': Pedido.objects.filter(estado='diseño').count(),
        'produccion': Pedido.objects.filter(estado='produccion').count(),
        'listos': Pedido.objects.filter(estado='listo').count(),
        'entregados': Pedido.objects.filter(estado='entregado').count(),
    }
    
    return render(request, 'sublimacion/dashboard.html', {
        'pedidos_recientes': pedidos_recientes,
        'estadisticas': estadisticas,
        'section': 'dashboard'
    })

@login_required
def crear_pedido(request):
    """Crear un nuevo pedido"""
    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        cantidad = int(request.POST.get('cantidad', 1))
        nombre_cliente = request.POST.get('nombre_cliente')
        telefono = request.POST.get('telefono', '')
        especificaciones = request.POST.get('especificaciones', '')
        abono = float(request.POST.get('abono', 0))
        
        producto = get_object_or_404(Producto, id=producto_id)
        precio_total = float(producto.precio_base) * cantidad
        
        # Verificar stock
        if producto.stock < cantidad:
            messages.error(request, f'Stock insuficiente. Solo hay {producto.stock} unidades')
            return redirect('crear_pedido_form')
        
        # Crear pedido
        pedido = Pedido.objects.create(
            nombre_cliente=nombre_cliente,
            telefono=telefono,
            producto=producto,
            cantidad=cantidad,
            especificaciones=especificaciones,
            precio_total=precio_total,
            abono=abono,
            registrado_por=request.user
        )
        
        # Reducir stock
        producto.stock -= cantidad
        producto.save()
        
        # ✅ Si hay abono inicial, registrar ingreso
        if abono > 0:
            from reportes.models import Ingreso
            Ingreso.objects.create(
                tipo='sublimacion_abono',
                monto=Decimal(str(abono)),
                descripcion=f'Abono inicial pedido #{pedido.id} - {nombre_cliente}',
                registrado_por=request.user,
                pedido_relacionado=pedido
            )
        
        messages.success(request, f'Pedido #{pedido.id} creado exitosamente')
        return redirect('detalle_pedido', pedido.id)
    
    # GET: Mostrar formulario
    productos = Producto.objects.all()
    return render(request, 'sublimacion/crear_pedido.html', {
        'productos': productos,
        'section': 'crear'
    })

@login_required
def crear_pedido_form(request):
    """Formulario para crear pedido"""
    productos = Producto.objects.all()
    return render(request, 'sublimacion/crear_pedido.html', {
        'productos': productos,
        'section': 'crear'
    })

@login_required
def detalle_pedido(request, id):
    """Ver detalles de un pedido"""
    pedido = get_object_or_404(Pedido, id=id)
    historial = pedido.historial.all()
    return render(request, 'sublimacion/detalle_pedido.html', {
        'pedido': pedido,
        'historial': historial,
        'saldo': pedido.saldo_pendiente()
    })

@login_required
@csrf_exempt
def cambiar_estado(request, id):
    """Cambiar estado del pedido - registra ingreso cuando se entrega"""
    from decimal import Decimal
    from reportes.models import Ingreso
    from django.utils import timezone
    
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=id)
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado and nuevo_estado != pedido.estado:
            estado_anterior = pedido.estado
            
            # Registrar en historial
            HistorialEstado.objects.create(
                pedido=pedido,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado,
                cambiado_por=request.user
            )
            
            pedido.estado = nuevo_estado
            
            # ✅ Cuando se entrega, registrar el pago final (saldo restante)
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

@login_required
def registrar_abono(request, id):
    """Registrar un abono al pedido"""
    from decimal import Decimal
    from reportes.models import Ingreso
    
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=id)
        
        try:
            monto = Decimal(str(request.POST.get('monto', 0)))
            
            if monto > 0 and monto <= pedido.saldo_pendiente():
                pedido.abono += monto
                pedido.save()
                
                # ✅ CORREGIDO: tipo 'sublimacion_abono' en lugar de 'abono'
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

@login_required
def gestionar_productos(request):
    """Gestionar productos (CRUD)"""
    productos = Producto.objects.all()
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        tipo = request.POST.get('tipo')
        precio_base = request.POST.get('precio_base')
        stock = request.POST.get('stock', 0)
        stock_minimo = request.POST.get('stock_minimo', 5)
        
        Producto.objects.create(
            nombre=nombre,
            tipo=tipo,
            precio_base=precio_base,
            stock=stock,
            stock_minimo=stock_minimo
        )
        messages.success(request, 'Producto agregado exitosamente')
        return redirect('gestionar_productos')
    
    return render(request, 'sublimacion/productos.html', {
        'productos': productos,
        'section': 'productos'
    })

@login_required
def editar_producto(request, id):
    """Editar un producto"""
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=id)
        producto.nombre = request.POST.get('nombre')
        producto.tipo = request.POST.get('tipo')
        producto.precio_base = request.POST.get('precio_base')
        producto.stock = request.POST.get('stock')
        producto.stock_minimo = request.POST.get('stock_minimo')
        producto.save()
        messages.success(request, 'Producto actualizado')
        return redirect('gestionar_productos')
    
    return redirect('gestionar_productos')

@login_required
def eliminar_producto(request, id):
    """Eliminar un producto"""
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=id)
        producto.delete()
        messages.success(request, 'Producto eliminado')
        return redirect('gestionar_productos')
    
    return redirect('gestionar_productos')