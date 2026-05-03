import asyncio
import logging
import os
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


def actualizar_divisas_soportadas(divisas_exitosas: set):
    """
    Reescribe modulos/divisas_list.py eliminando las divisas que NO se pudieron
    extraer en esta ejecución (no devolvieron datos válidos desde Google Finance).
    Solo actúa si el porcentaje de éxito es >= 50% del total de divisas soportadas,
    para evitar degradar la lista por bloqueos temporales de Google Finance.
    """
    divisas_actuales = set(DIVISAS_SOPORTADAS)
    total_esperadas = len(divisas_actuales)
    exitosas_sin_usd = divisas_exitosas - {"USD"}

    # Umbral de seguridad: solo limpiar la lista si al menos el 50% tuvo éxito
    if len(exitosas_sin_usd) < total_esperadas * 0.5:
        logger.warning(
            f"Solo {len(exitosas_sin_usd)}/{total_esperadas} divisas se extrajeron exitosamente "
            f"({len(exitosas_sin_usd)/total_esperadas*100:.1f}%). "
            f"Umbral mínimo (50%) no alcanzado. Se conserva divisas_list.py sin cambios."
        )
        return

    divisas_removidas = divisas_actuales - divisas_exitosas - {"USD"}  # USD es manual

    if not divisas_removidas:
        logger.info("Todas las divisas se extrajeron exitosamente. No se eliminaron divisas de la lista.")
        return

    logger.warning(f"Eliminando {len(divisas_removidas)} divisas no disponibles: {sorted(divisas_removidas)}")

    divisas_nuevas = sorted(divisas_exitosas | {"USD"})

    # Reconstruir el archivo divisas_list.py
    ruta = os.path.join(os.path.dirname(__file__), "modulos", "divisas_list.py")
    lineas = ["# Lista de todas las divisas para consultar su valor contra el USD en Google Finance.\n"]
    lineas.append("DIVISAS_SOPORTADAS = [\n")
    # Escribir en filas de 12 por linea para mejor legibilidad
    chunk = 12
    for i in range(0, len(divisas_nuevas), chunk):
        fila = divisas_nuevas[i:i+chunk]
        lineas.append("    " + ", ".join(f'"{d}"' for d in fila) + ("," if i + chunk < len(divisas_nuevas) else "") + "\n")
    lineas.append("]\n")

    with open(ruta, "w", encoding="utf-8") as f:
        f.writelines(lineas)

    logger.info(f"divisas_list.py actualizado con {len(divisas_nuevas)} divisas disponibles.")


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
    divisas_exitosas = set()  # Guardamos los códigos que sí tuvieron datos
    
    # B. Comparar / Parsear usando clase Decimal
    for url, html_crudo in resultados_html.items():
        codigo_divisa = urls_a_consultar[url]
        divisa_data = comparer.snapshot_scraping_individual(html_crudo, codigo=codigo_divisa)
        if divisa_data:
            divisas_extraidas.append(divisa_data)
            divisas_exitosas.add(codigo_divisa)

    # Validar que hay suficientes divisas antes de continuar
    # (un número bajo indica bloqueo de Google Finance)
    MINIMO_DIVISAS_VALIDAS = 10
    if len(divisas_extraidas) < MINIMO_DIVISAS_VALIDAS:
        logger.error(
            f"Solo se extrajeron {len(divisas_extraidas)} divisas válidas (mínimo requerido: {MINIMO_DIVISAS_VALIDAS}). "
            f"Posible bloqueo de Google Finance. Se aborta para no sobrescribir datos.json con datos incompletos."
        )
        return

    # Añadimos USD manualmente como referencia base (valor 1:1)
    divisas_extraidas.append({
        "codigo": "USD-USD",
        "valor_comparacion": "USD",
        "valor_actual": Decimal('1.0')
    })
    divisas_exitosas.add("USD")
        
    logger.info(f"Guardando {len(divisas_extraidas)} registros en la base de datos...")
    
    # C. Limpiar tabla y guardar datos frescos (evitar acumulacion de datos obsoletos)
    db_manager.limpiar_tabla()
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

    # 4. Remover divisas no disponibles de la lista de soportadas
    actualizar_divisas_soportadas(divisas_exitosas)
    
    logger.info("Proceso completado exitosamente.")

if __name__ == "__main__":
    asyncio.run(main())
