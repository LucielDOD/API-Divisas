import asyncio
import random
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import logging

logger = logging.getLogger(__name__)

# --- Configuración anti-detección ---
# Tamaño de cada lote de URLs a procesar consecutivamente
BATCH_SIZE = 3
# Rango de delay (en segundos) entre lotes para simular pausa humana
DELAY_ENTRE_LOTES_MIN = 5
DELAY_ENTRE_LOTES_MAX = 20
# Selector CSS del precio en Google Finance (para detectar bloqueos)
SELECTOR_PRECIO = 'div.YMlKec.fxKbKc'
# Pool de User-Agents para rotar por sesión
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15',
]


async def extract_html_from_url(url: str) -> str:
    """Extrae el HTML crudo de una URL individual esperando a que la red esté inactiva."""
    html_content = ""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
        page = await context.new_page()
        try:
            logger.info(f"Navegando a {url}...")
            await page.goto(url, wait_until='networkidle', timeout=60000)
            html_content = await page.content()
            logger.info(f"HTML extraído exitosamente (Longitud: {len(html_content)} bytes).")
        except PlaywrightTimeoutError:
            logger.error(f"Timeout al intentar acceder a {url}.")
        except Exception as e:
            logger.error(f"Error procesando {url}: {e}")
        finally:
            await browser.close()

    return html_content


async def extract_html_multiple_urls(urls: list[str]) -> dict[str, str]:
    """Extrae el HTML de múltiples URLs usando scraping por lotes para evitar bloqueos.

    Estrategia anti-detección:
    - Procesa las URLs en lotes de BATCH_SIZE (default: 5)
    - Entre cada lote espera un delay aleatorio de DELAY_ENTRE_LOTES_MIN a DELAY_ENTRE_LOTES_MAX segundos
    - Rota el User-Agent al iniciar cada lote (nueva sesión de contexto)
    - Registra una advertencia si Google Finance no devuelve el div de precio (posible bloqueo)
    """
    results = {}
    total = len(urls)
    # Dividir la lista en lotes de BATCH_SIZE
    lotes = [urls[i:i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    total_lotes = len(lotes)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        urls_procesadas = 0
        for num_lote, lote in enumerate(lotes, start=1):
            logger.info(f"--- [Lote {num_lote}/{total_lotes}] Iniciando ({len(lote)} URLs) ---")

            # Crear un nuevo contexto (nueva sesión/cookies) con User-Agent aleatorio por lote
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()

            for url in lote:
                urls_procesadas += 1
                try:
                    logger.info(f"  [{urls_procesadas}/{total}] Extrayendo: {url}")
                    await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                    html_content = await page.content()

                    # Detectar si Google devolvió una página sin precio (posible bloqueo)
                    if SELECTOR_PRECIO not in html_content:
                        logger.warning(f"  [Posible bloqueo] No se encontró div de precio en: {url}")

                    results[url] = html_content

                except PlaywrightTimeoutError:
                    logger.error(f"  Timeout procesando: {url}")
                except Exception as e:
                    logger.error(f"  Error procesando {url}: {e}")

            await context.close()

            # Pausa entre lotes (excepto después del último)
            if num_lote < total_lotes:
                delay = random.uniform(DELAY_ENTRE_LOTES_MIN, DELAY_ENTRE_LOTES_MAX)
                logger.info(f"--- [Lote {num_lote}/{total_lotes}] Completado. Esperando {delay:.1f}s antes del siguiente lote... ---")
                await asyncio.sleep(delay)

        await browser.close()

    logger.info(f"Extracción finalizada. {len(results)}/{total} URLs procesadas exitosamente.")
    return results
