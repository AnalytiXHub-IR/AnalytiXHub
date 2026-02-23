import asyncio
from playwright.async_api import async_playwright
import time
import requests

async def test_charts():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture console logs
        page.on("console", lambda msg: print(f"Browser Console: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser Error: {err}"))
        
        # Need to simulate login or bypass it.
        # Bypass easiest: post directly to /login
        print("Logging in...")
        await page.goto("http://127.0.0.1:5000/login")
        await page.fill("input[name='username']", "admin")
        await page.fill("input[name='password']", "password")
        await page.click("button[type='submit']")
        
        print("Creating an active case...")
        await page.goto("http://127.0.0.1:5000/")
        await page.evaluate("""
            fetch('/case/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'case_name=Test+Case&description=TEST'
            });
        """)
        await page.wait_for_timeout(1000)
        
        print("Navigating to Investigation...")
        await page.goto("http://127.0.0.1:5000/investigation")
        await page.fill("input[name='address']", "0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
        await page.click("button:has-text('Analyze Address')")
        
        print("Waiting to load and clicking charts tab...")
        await page.wait_for_timeout(3000) # wait for page load after post
        await page.evaluate("document.getElementById('charts-tab').click()")
        await page.wait_for_timeout(2000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_charts())
