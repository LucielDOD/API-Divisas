import asyncio
import logging
import sys
from decimal import Decimal
from modulos.Actualizacion_bd import DatabaseManager
from modulos.Extraccion_front import extract_html_multiple_urls
from modulos.Comparacion_front import ContentComparer
from modulos.divisas_list import DIVISAS_SOPORTADAS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Iniciando orquestación de la API de Divisas...")
    
    # 1. Inicializar DB y Comparador
    db_manager = DatabaseManager()
    comparer = ContentComparer()

    logger.info(f"=== Preparando {len(DIVISAS_SOPORTADAS)} divisas para extracción ===")
    
    # Generar URLs a consultar (Ej: https://www.google.com/finance/quote/EUR-USD?hl=es)
    # Evitamos USD-USD
    urls_a_consultar = {}
    for divisa in set(DIVISAS_SOPORTADAS):
        if divisa == "USD": 
            continue
        url = f"https://www.google.com/finance/quote/{divisa}-USD?hl=es"
        urls_a_consultar[url] = divisa

    urls_list = list(urls_a_consultar.keys())
    
    # A. Extraer multi-URLs (Esto devolverá un diccionario {url: html_content})
    resultados_html = await extract_html_multiple_urls(urls_list)
    
    if not resultados_html:
        logger.error(f"No se obtuvieron resultados de la extracción de URLs. Abortando.")
        return
        
    divisas_extraidas = []
    
    # B. Comparar / Parsear usando clase Decimal
    for url, html_crudo in resultados_html.items():
        codigo_divisa = urls_a_consultar[url]
        divisa_data = comparer.snapshot_scraping_individual(html_crudo, codigo=codigo_divisa)
        if divisa_data:
            divisas_extraidas.append(divisa_data)
            
    # Añadimos USD manualmente por si se necesita de base
    divisas_extraidas.append({
        "codigo": "USD-USD",
        "valor_comparacion": "USD",
        "valor_actual": Decimal('1.0')
    })
    
    if not divisas_extraidas:
        logger.warning(f"No se extrajeron divisas válidas. Verifica la estructura del HTML.")
        return
        
    logger.info(f"Guardando {len(divisas_extraidas)} registros en la base de datos...")
    
    # C. Guardar en Base de Datos
    for divisa in divisas_extraidas:
        codigo_db = divisa["codigo"] # e.g. "EUR-USD"
        comparacion = divisa["valor_comparacion"]
        valor_actual = divisa["valor_actual"]
        
        # Para Google Finance individual, el precio es el relativo directo.
        total_calc = comparer.calculate_relative_value(valor_actual, Decimal('1.0'))
        
        db_manager.upsert_divisa(
            codigo=codigo_db,
            valor_actual=valor_actual,
            valor_comparacion=comparacion,
            total_calculado=total_calc
        )
    
    # 3. Exportar resultados al JSON
    logger.info("Exportando datos a datos.json...")
    db_manager.export_to_json("datos.json")
    
    logger.info("Proceso completado exitosamente.")

if __name__ == "__main__":
    asyncio.run(main())
