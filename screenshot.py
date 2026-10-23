import asyncio
from playwright.async_api import async_playwright
import os
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

async def take_screenshots():
    # Start simple HTTP server in background thread - serve from dist/
    os.chdir('D:/intel-daily-astro/dist')
    server = HTTPServer(('127.0.0.1', 8765), SimpleHTTPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)  # Give server time to start
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            
            pages = [
                ('index', 'http://127.0.0.1:8765/index.html'),
                ('hot', 'http://127.0.0.1:8765/hot/index.html'),
                ('day', 'http://127.0.0.1:8765/day/2026-10-23/index.html'),
                ('new-terms', 'http://127.0.0.1:8765/new-terms/index.html'),
                ('officer', 'http://127.0.0.1:8765/officer/index.html'),
            ]
            
            output_dir = 'D:/intel-daily-astro/screenshots'
            os.makedirs(output_dir, exist_ok=True)
            
            for name, url in pages:
                print(f'Taking screenshot of {name}...')
                # Desktop
                context = await browser.new_context(viewport={'width': 1440, 'height': 900})
                page = await context.new_page()
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                await page.screenshot(path=os.path.join(output_dir, f'{name}-desktop.png'), full_page=False)
                await context.close()
                print(f'  Desktop OK')
                
                # Mobile
                context = await browser.new_context(viewport={'width': 390, 'height': 844})
                page = await context.new_page()
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                await page.screenshot(path=os.path.join(output_dir, f'{name}-mobile.png'), full_page=False)
                await context.close()
                print(f'  Mobile OK')
            
            await browser.close()
            print('All screenshots generated!')
    finally:
        server.shutdown()

asyncio.run(take_screenshots())
