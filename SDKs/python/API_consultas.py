import requests
from decimal import Decimal
from datetime import datetime

# El "mesero" conoce exactamente en qué parte del restaurante (GitHub) están los ingredientes.
# El cliente no necesita saber esta dirección.
URL_DATOS_GITHUB = "https://LucielDOD.github.io/API-Divisas/datos.json"

def Solicitar_Divisas_Disponibles() -> dict:
    """
    Obtiene la lista de códigos de divisas disponibles leyendo el JSON remoto.
    Retorna un diccionario con la respuesta formateada.
    """
    try:
        response = requests.get(URL_DATOS_GITHUB)
        response.raise_for_status()
        data = response.json()
        
        # Extraer códigos, removiendo el sufijo '-USD' (Ej: 'EUR-USD' -> 'EUR')
        codigos = [d["codigo"].replace("-USD", "") for d in data]
        codigos = sorted(list(set(codigos)))
        
        return {
            "status": "success",
            "cantidad": len(codigos),
            "divisas": codigos,
            "fecha_consulta": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        }
    except Exception as e:
        return {
            "status": "error",
            "mensaje": f"Error al obtener divisas disponibles: {str(e)}"
        }

def Solicitar_Valor_Divisa(divisa_1: str, divisa_2: str) -> dict:
    """
    Calcula el valor de divisa_1 expresado en divisa_2 extrayendo los datos remotamente.
    Retorna un diccionario con la respuesta formateada simulando una API REST.
    """
    divisa_1 = divisa_1.upper()
    divisa_2 = divisa_2.upper()

    try:
        # Descarga los precios de github
        response = requests.get(URL_DATOS_GITHUB)
        response.raise_for_status()
        data = response.json()
        
        # Mapeamos los datos { "EUR": Decimal("1.08"), ... }
        valores_en_usd = { 
            d["codigo"].replace("-USD", ""): Decimal(str(d["valor_actual"])) 
            for d in data 
        }
        
        if divisa_1 not in valores_en_usd:
            return {"status": "error", "mensaje": f"La divisa base '{divisa_1}' no se encuentra en el origen de datos."}
        if divisa_2 not in valores_en_usd:
            return {"status": "error", "mensaje": f"La divisa objetivo '{divisa_2}' no se encuentra en el origen de datos."}
            
        valor_1 = valores_en_usd[divisa_1]
        valor_2 = valores_en_usd[divisa_2]
        
        # (Divisa 1 a USD) / (Divisa 2 a USD)
        resultado = valor_1 / valor_2
        
        return {
            "status": "success",
            "codigo": f"{divisa_1}-{divisa_2}",
            "valor": round(float(resultado), 4),
            "divisa_base": divisa_1,
            "divisa_objetivo": divisa_2,
            "fecha_consulta": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        }

    except Exception as e:
        return {
            "status": "error",
            "mensaje": f"Error al calcular divisas: {str(e)}"
        }
