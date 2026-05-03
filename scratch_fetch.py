import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.google.com/finance/quote/EUR-USD?hl=es")
        content = await page.content()
        with open("plantilla3.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("HTML guardado en plantilla3.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
