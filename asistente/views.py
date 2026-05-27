from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum
from estaciones.models import Estacion
from sublimacion.models import Pedido
from inventario.models import Insumo
import json
from datetime import datetime

@login_required
def asistente_view(request):
    """Vista del asistente de IA"""
    return render(request, 'asistente/asistente.html')

@login_required
def api_asistente(request):
    """API del asistente para responder preguntas"""
    if request.method == 'POST':
        data = json.loads(request.body)
        pregunta = data.get('pregunta', '').lower()
        
        # Estadísticas en tiempo real
        estaciones_libres = Estacion.objects.filter(estado='libre').count()
        pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
        pedidos_produccion = Pedido.objects.filter(estado='produccion').count()
        
        # Diccionario de respuestas
        respuestas = {
            'ventas': f"💰 Las ventas de hoy son: Consulta el módulo de Reportes → Ventas para ver el detalle completo.",
            'stock': f"📦 Revisa el módulo de Inventario para ver el stock actual de todos los insumos.",
            'pcs': f"🖥️ Actualmente hay {estaciones_libres} PCs libres de {Estacion.objects.count()} totales.",
            'pedidos': f"📋 Hay {pedidos_pendientes} pedidos pendientes y {pedidos_produccion} en producción.",
            'ayuda': "🤖 Soy tu asistente. Puedo ayudarte con:\n• ventas - Resumen de ventas\n• stock - Estado del inventario\n• pcs - PCs disponibles\n• pedidos - Estado de pedidos",
            'hola': "¡Hola! ¿En qué puedo ayudarte hoy?",
            'gracias': "¡De nada! Estoy aquí para ayudarte cuando lo necesites."
        }
        
        respuesta = "🤖 No entendí tu pregunta. Escribe 'ayuda' para ver qué puedo hacer."
        
        for key, value in respuestas.items():
            if key in pregunta:
                respuesta = value
                break
        
        return JsonResponse({'respuesta': respuesta})
    
    return JsonResponse({'respuesta': 'Método no permitido'}, status=405)

