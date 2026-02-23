import asyncio
import logging
import sys
from decimal import Decimal
from modulos.Actualizacion_bd import DatabaseManager
from modulos.Extraccion_front import extract_html_from_url
from modulos.Comparacion_front import ContentComparer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# URL principal de scraping (Google Finance)
SOURCE_URL = "https://www.google.com/finance/markets/currencies?hl=es"

async def main():
    logger.info("Iniciando orquestación de la API de Divisas...")
    
    # 1. Inicializar DB y Comparador
    db_manager = DatabaseManager()
    comparer = ContentComparer()

    logger.info(f"=== Extrayendo datos desde: {SOURCE_URL} ===")
    
    # A. Extraer
    html_crudo = await extract_html_from_url(SOURCE_URL)
    
    if not html_crudo:
        logger.error(f"No se pudo obtener el HTML para la URL principal. Abortando.")
        return
        
    # B. Comparar / Parsear usando clase Decimal
    # Extrae todos los pares de divisas presentes
    divisas_extraidas = comparer.snapshot_scraping(html_crudo)
    
    if not divisas_extraidas:
        logger.warning(f"No se extrajeron divisas válidas. Verifica la estructura del HTML en snapshot_scraping.")
        return
        
    logger.info(f"Guardando {len(divisas_extraidas)} registros en la base de datos...")
    
    # C. Guardar en Base de Datos
    for divisa in divisas_extraidas:
        codigo = divisa["codigo"]
        comparacion = divisa["valor_comparacion"]
        valor_actual = divisa["valor_actual"]
        
        # Opcional: calcular un relativo utilizando el factor. Para Google Finance es 1:1 ya que el precio *ES* la comparación.
        total_calc = comparer.calculate_relative_value(valor_actual, Decimal('1.0'))
        
        # Almacenamos el código como un par completo para evitar sobreescritura (e.g., 'EUR/USD' en vez de solo 'EUR')
        # Esto porque Google Finance da EUR/USD, EUR/JPY, etc.
        codigo_db = f"{codigo}/{comparacion}"
        
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
