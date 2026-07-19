from decimal import Decimal
from .models import TasaCambio

def obtener_tasa_bcv():
    """
    Obtiene la tasa de cambio del BCV desde la API de TasaVE.
    """
    try:
        from tasave import TasaVE
        client = TasaVE()
        rate_obj = client.rates.bcv()
        
        # El objeto BcvRate puede tener atributos como 'price' o 'value'
        # Intentamos extraer el valor numérico
        if hasattr(rate_obj, 'price'):
            return Decimal(str(rate_obj.price))
        elif hasattr(rate_obj, 'value'):
            return Decimal(str(rate_obj.value))
        elif hasattr(rate_obj, 'rate'):
            return Decimal(str(rate_obj.rate))
        else:
            # Si no tiene atributos conocidos, intentamos convertirlo a float
            return Decimal(str(float(rate_obj)))
    except ImportError:
        # Fallback: intentar con requests
        try:
            import requests
            response = requests.get("https://api.tasave.com/v1/rates/bcv", timeout=10)
            if response.status_code == 200:
                data = response.json()
                valor = data.get('rate') or data.get('value') or data.get('price')
                if valor:
                    return Decimal(str(valor))
        except:
            pass
    except Exception as e:
        print(f"Error al obtener tasa: {e}")
    return None

def actualizar_tasa_automatica():
    """Actualiza la tasa en la base de datos con la última de la API."""
    tasa = obtener_tasa_bcv()
    if tasa:
        TasaCambio.objects.create(tasa=tasa, fuente='API TasaVE')
        print(f"✅ Tasa actualizada a {tasa}")
        return True
    print("ℹ️ No se pudo actualizar desde la API. La última tasa registrada se mantiene.")
    return False