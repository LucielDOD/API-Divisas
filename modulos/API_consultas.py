import requests
from decimal import Decimal

# Eliminamos la URL hardcodeada de aquí para que sea el usuario/cliente (prueba_api) 
# quien le diga a nuestra API dónde ir a buscar los datos.

def Solicitar_Divisas_Disponibles(url_origen: str) -> list:
    """
    Obtiene la lista de códigos de divisas disponibles leyendo el JSON remoto.
    """
    if not url_origen:
        print("Error: Se requiere una URL de origen válida.")
        return []
        
    try:
        response = requests.get(url_origen)
        response.raise_for_status()
        data = response.json()
        
        # Extraer códigos, removiendo el sufijo '-USD' (Ej: 'EUR-USD' -> 'EUR')
        codigos = [d["codigo"].replace("-USD", "") for d in data]
        # Remover duplicados y ordenar
        return sorted(list(set(codigos)))
    except Exception as e:
        print(f"Error al obtener divisas disponibles: {e}")
        return []

def Solicitar_Valor_Divisa(divisa_1: str, divisa_2: str, url_origen: str) -> Decimal:
    """
    Calcula el valor de divisa_1 expresado en divisa_2 extrayendo los datos remotamente.
    La fuente almacena todo respecto a USD.
    Por lo tanto: divisa_1 a divisa_2 = (Valor divisa_1 en USD) / (Valor divisa_2 en USD)
    EJ: Solicitar_Valor_Divisa('EUR', 'CLP', url_origen='https://...')
    """
    if not url_origen:
        print("Error: Se requiere una URL de origen válida.")
        return Decimal('0')
        
    divisa_1 = divisa_1.upper()
    divisa_2 = divisa_2.upper()

    try:
        # Descarga los precios de github
        response = requests.get(url_origen)
        response.raise_for_status()
        data = response.json()
        
        # Mapeamos los datos { "EUR": Decimal("1.08"), ... }
        valores_en_usd = { 
            d["codigo"].replace("-USD", ""): Decimal(str(d["valor_actual"])) 
            for d in data 
        }
        
        if divisa_1 not in valores_en_usd:
            raise ValueError(f"La divisa base '{divisa_1}' no se encuentra en el origen de datos.")
        if divisa_2 not in valores_en_usd:
            raise ValueError(f"La divisa objetivo '{divisa_2}' no se encuentra en el origen de datos.")
            
        valor_1 = valores_en_usd[divisa_1]
        valor_2 = valores_en_usd[divisa_2]
        
        # (Divisa 1 a USD) / (Divisa 2 a USD)
        resultado = valor_1 / valor_2
        return resultado

    except requests.exceptions.RequestException as e:
        print(f"Error de red al consultar los datos: {e}")
        return Decimal('0')
    except Exception as e:
        print(f"Error al calcular divisas: {e}")
        return Decimal('0')
