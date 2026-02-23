import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import logging

logger = logging.getLogger(__name__)

async def extract_html_from_url(url: str) -> str:
    """Extrae el HTML crudo de una URL esperando a que la red esté inactiva."""
    html_content = ""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        try:
            # Ir a la página y esperar hasta que las peticiones de red queden inactivas
            logger.info(f"Navegando a {url}...")
            await page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Obtener el contenido HTML crudo
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
    """Extrae el HTML de múltiples URLs reutilizando la misma sesión del navegador."""
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        for i, url in enumerate(urls):
            try:
                logger.info(f"[{i+1}/{len(urls)}] Extrayendo: {url}")
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                # Esperar 1 segundo por si acaso para no ser bloqueados
                await asyncio.sleep(1)
                
                html_content = await page.content()
                results[url] = html_content
            except PlaywrightTimeoutError:
                logger.error(f"Timeout procesando {url}.")
            except Exception as e:
                logger.error(f"Error procesando {url}: {e}")
                
        await browser.close()
    return results
