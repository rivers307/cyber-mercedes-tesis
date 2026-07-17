# reportes/management/commands/cargar_precios.py
from django.core.management.base import BaseCommand
from reportes.models import PrecioServicio

class Command(BaseCommand):
    help = 'Carga precios iniciales de servicios en USD'

    def handle(self, *args, **options):
        precios = [
            ('pc_hora', '🖥️ PC por Hora', 1.50),
            ('sublimacion_taza', '🎨 Taza Sublimada', 8.00),
            ('sublimacion_camiseta', '👕 Camiseta Sublimada', 15.00),
            ('sublimacion_gorra', '🧢 Gorra Sublimada', 10.00),
            ('sublimacion_termo', '🫖 Termo Sublimado', 12.00),
            ('impresion_bn', '📄 Impresión B/N', 0.10),
            ('impresion_color', '🎨 Impresión Color', 0.30),
            ('fotocopia_bn', '📋 Fotocopia B/N', 0.05),
            ('fotocopia_color', '📋 Fotocopia Color', 0.20),
            ('insumo_venta', '📦 Venta de Insumo', 0.00),  # precio variable
            ('servicio_extra', '🔧 Servicio Extra', 5.00),
        ]

        for servicio, nombre, precio in precios:
            PrecioServicio.objects.update_or_create(
                servicio=servicio,
                defaults={
                    'nombre_mostrar': nombre,
                    'precio_usd': precio,
                    'activo': True,
                }
            )
            self.stdout.write(f'✅ Cargado: {nombre} - ${precio} USD')

        self.stdout.write(self.style.SUCCESS('✅ Precios cargados exitosamente'))