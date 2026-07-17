from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, F
from estaciones.models import Estacion
from sublimacion.models import Pedido, Producto
from inventario.models import Insumo, MovimientoInventario
from reportes.models import Ingreso
from django.utils import timezone
from usuarios.decorators import empleado_required
import json
from datetime import datetime, timedelta

# ========== VISTA DEL ASISTENTE ==========
@empleado_required
def asistente_view(request):
    """Vista del asistente de IA"""
    return render(request, 'asistente/asistente.html')


# ========== API DEL ASISTENTE (VERSIÓN LOCAL) ==========
@empleado_required
def api_asistente(request):
    """API del asistente para responder preguntas - Versión Local"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pregunta = data.get('pregunta', '').lower()
            
            # ========== DATOS EN TIEMPO REAL ==========
            hoy = timezone.now().date()
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            inicio_mes = hoy.replace(day=1)
            
            # --- ESTACIONES ---
            total_pcs = Estacion.objects.count()
            pcs_libres = Estacion.objects.filter(estado='libre').count()
            pcs_ocupadas = Estacion.objects.filter(estado='ocupada').count()
            pcs_mantenimiento = Estacion.objects.filter(estado='mantenimiento').count()
            
            # --- PEDIDOS ---
            pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
            pedidos_produccion = Pedido.objects.filter(estado='produccion').count()
            pedidos_listos = Pedido.objects.filter(estado='listo').count()
            pedidos_entregados = Pedido.objects.filter(estado='entregado').count()
            total_pedidos = Pedido.objects.count()
            
            # --- VENTAS ---
            ventas_hoy = Ingreso.objects.filter(fecha__date=hoy).aggregate(total=Sum('monto'))['total'] or 0
            ventas_semana = Ingreso.objects.filter(fecha__date__gte=inicio_semana).aggregate(total=Sum('monto'))['total'] or 0
            ventas_mes = Ingreso.objects.filter(fecha__date__gte=inicio_mes).aggregate(total=Sum('monto'))['total'] or 0
            
            # --- PRODUCTOS ---
            productos_populares = Producto.objects.annotate(
                total_vendidos=Sum('pedido__cantidad')
            ).filter(total_vendidos__gt=0).order_by('-total_vendidos')[:5]
            
            productos_texto = ""
            for p in productos_populares:
                productos_texto += f"   • {p.nombre}: {p.total_vendidos} unidades\n"
            
            if not productos_texto:
                productos_texto = "   • Sin ventas aún\n"
            
            # --- INSUMOS ---
            insumos_bajos = Insumo.objects.filter(stock_actual__lte=F('stock_minimo'))
            insumos_texto = ""
            for i in insumos_bajos[:5]:
                insumos_texto += f"   • {i.nombre}: {i.stock_actual} (mínimo: {i.stock_minimo})\n"
            
            if not insumos_texto:
                insumos_texto = "   • Ningún insumo con stock bajo\n"
            
            # ========== RESPUESTAS ==========
            respuesta = "🤖 No entendí tu pregunta. Escribe **'ayuda'** para ver todos los comandos disponibles."
            
            # Ventas
            if any(word in pregunta for word in ['ventas', 'ganancias', 'ingresos', 'caja', 'dinero']):
                respuesta = f"💰 **Ventas:**\n   • Hoy: Bs {ventas_hoy:.2f}\n   • Esta semana: Bs {ventas_semana:.2f}\n   • Este mes: Bs {ventas_mes:.2f}"
                
            # PCs
            elif any(word in pregunta for word in ['pcs', 'computadoras', 'equipos', 'estaciones', 'pc']):
                respuesta = f"🖥️ **Estado de las PCs:**\n   • Total: {total_pcs}\n   • 🟢 Libres: {pcs_libres}\n   • 🔴 Ocupadas: {pcs_ocupadas}\n   • 🟡 Mantenimiento: {pcs_mantenimiento}"
            
            # Pedidos
            elif any(word in pregunta for word in ['pedidos', 'ordenes', 'sublimación', 'trabajos']):
                respuesta = f"📋 **Estado de pedidos de sublimación:**\n   • 📋 Pendientes: {pedidos_pendientes}\n   • 🖨️ En producción: {pedidos_produccion}\n   • ✅ Listos para entregar: {pedidos_listos}\n   • 🎁 Entregados: {pedidos_entregados}\n   • Total: {total_pedidos}"
            
            # Pendientes
            elif any(word in pregunta for word in ['pendientes', 'pendiente']):
                respuesta = f"📋 **Pedidos pendientes:** {pedidos_pendientes}"
            
            # Producción
            elif any(word in pregunta for word in ['produccion', 'fabricando']):
                respuesta = f"🖨️ **Pedidos en producción:** {pedidos_produccion}"
            
            # Stock / Inventario
            elif any(word in pregunta for word in ['stock', 'inventario', 'insumos', 'materiales']):
                respuesta = f"📦 **Resumen de stock:**\n   • Total insumos: {Insumo.objects.count()}\n   • Stock bajo: {insumos_bajos.count()}\n   • Sin stock: {Insumo.objects.filter(stock_actual=0).count()}\n\n⚠️ **Insumos con stock bajo:**\n{insumos_texto}"
            
            # Productos
            elif any(word in pregunta for word in ['productos', 'populares', 'top', 'vendidos', 'mas vendidos']):
                respuesta = f"🏆 **Productos más vendidos:**\n{productos_texto}"
            
            # Ayuda
            elif any(word in pregunta for word in ['ayuda', 'comandos', 'opciones', 'que puedes hacer', 'que haces']):
                respuesta = """🤖 **Comandos disponibles:**

📊 **Ventas:** ventas, ganancias, ingresos
🖥️ **PCs:** pcs, computadoras, estado
📋 **Pedidos:** pedidos, pendientes, sublimación
🏆 **Productos:** productos, populares, top
📦 **Stock:** stock, inventario, insumos

*Ejemplos:* "¿Cómo van las ventas?", "Estado de las PCs", "Pedidos pendientes" """
            
            # Saludo
            elif any(word in pregunta for word in ['hola', 'buenos', 'buenas', 'hello', 'hey', 'saludos']):
                respuesta = "¡Hola! 👋 Soy tu asistente virtual. Escribe **'ayuda'** para ver todos los comandos disponibles."
            
            # Gracias
            elif any(word in pregunta for word in ['gracias', 'gracias', 'gracias']):
                respuesta = "¡De nada! 😊 Estoy aquí para ayudarte. ¿Necesitas algo más?"
            
            return JsonResponse({'respuesta': respuesta})
            
        except Exception as e:
            return JsonResponse({
                'respuesta': f'❌ Error: {str(e)}'
            }, status=500)
    
    return JsonResponse({'respuesta': 'Método no permitido'}, status=405)