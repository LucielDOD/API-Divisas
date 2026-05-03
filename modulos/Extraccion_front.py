import asyncio
import random
import requests
import logging

logger = logging.getLogger(__name__)

# --- Configuración anti-detección (Requests) ---
# Tamaño de cada lote de URLs a procesar consecutivamente
BATCH_SIZE = 5
# Rango de delay (en segundos) entre lotes para simular pausa humana
DELAY_ENTRE_LOTES_MIN = 3
DELAY_ENTRE_LOTES_MAX = 8
# Selector CSS del precio en Google Finance (para detectar bloqueos)
SELECTOR_PRECIO = 'YMlKec fxKbKc'

# Headers base para que la petición de requests sea más natural
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
}


def _fetch_url_sync(url: str) -> str:
    """Función síncrona para descargar el HTML usando requests."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Error procesando {url}: {e}")
        return ""


async def extract_html_from_url(url: str) -> str:
    """Extrae el HTML crudo de una URL de forma asíncrona usando requests en otro hilo."""
    logger.info(f"Navegando a {url} con Requests...")
    html_content = await asyncio.to_thread(_fetch_url_sync, url)
    if html_content:
        logger.info(f"HTML extraído exitosamente (Longitud: {len(html_content)} bytes).")
    return html_content


async def extract_html_multiple_urls(urls: list[str]) -> dict[str, str]:
    """Extrae el HTML de múltiples URLs usando peticiones HTTP directas (Requests).
    
    Es mucho más rápido que Playwright y evita que Google Finance oculte el 
    div del precio por detección de navegador Headless.
    """
    results = {}
    total = len(urls)
    
    # Dividir la lista en lotes de BATCH_SIZE
    lotes = [urls[i:i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    total_lotes = len(lotes)

    urls_procesadas = 0
    for num_lote, lote in enumerate(lotes, start=1):
        logger.info(f"--- [Lote {num_lote}/{total_lotes}] Iniciando ({len(lote)} URLs) ---")

        # Lanzamos las peticiones del lote en paralelo usando hilos
        tareas = [asyncio.to_thread(_fetch_url_sync, url) for url in lote]
        htmls = await asyncio.gather(*tareas)

        for url, html_content in zip(lote, htmls):
            urls_procesadas += 1
            if html_content:
                # Detectar si Google devolvió una página sin precio (posible bloqueo)
                if SELECTOR_PRECIO not in html_content:
                    logger.warning(f"  [Posible bloqueo] No se encontró clase de precio en: {url}")
                results[url] = html_content
            
            logger.info(f"  [{urls_procesadas}/{total}] Extraído: {url}")

        # Pausa entre lotes (excepto después del último)
        if num_lote < total_lotes:
            delay = random.uniform(DELAY_ENTRE_LOTES_MIN, DELAY_ENTRE_LOTES_MAX)
            logger.info(f"--- [Lote {num_lote}/{total_lotes}] Esperando {delay:.1f}s antes del siguiente lote... ---")
            await asyncio.sleep(delay)

    logger.info(f"Extracción finalizada. {len(results)}/{total} URLs procesadas exitosamente.")
    return results
