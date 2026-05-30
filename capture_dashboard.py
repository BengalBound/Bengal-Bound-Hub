import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bengalbound_core.settings.development')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Create test user if it doesn't exist
username = 'playwright_tester'
password = 'testpassword123'
email = 'playwright@bengalbound.com'

try:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
except User.DoesNotExist:
    user = User.objects.create_superuser(username, email, password)
    # Give them workspace admin role or whatever is needed to see console
    if hasattr(user, 'role'):
        user.role = 'workspace_admin'
        user.save()

print(f"Created/updated user: {username}")

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Desktop
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        # Login
        print("Logging in...")
        await page.goto("http://127.0.0.1:8000/accounts/login/")
        
        # Check what fields exist (id_login usually for allauth)
        if await page.locator("input[name='login']").count() > 0:
            await page.fill("input[name='login']", username)
        else:
            await page.fill("input[name='username']", username)
            
        await page.fill("input[name='password']", password)
        await page.click("button[type='submit']")
        
        # Wait for redirect to console
        print("Waiting for dashboard to load...")
        try:
            await page.wait_for_url("**/console/**", timeout=10000)
        except Exception:
            # If not redirected automatically, go there manually
            await page.goto("http://127.0.0.1:8000/console/")
            await page.wait_for_load_state("networkidle")
            
        # Hide any debug toolbar or sticky footers that might ruin the shot
        await page.evaluate("""
            if (document.getElementById('djDebug')) document.getElementById('djDebug').style.display = 'none';
        """)
        
        # Desktop screenshot
        print("Taking desktop screenshot...")
        await page.screenshot(path="static/img/desktop_dashboard.png")
        
        # Mobile screenshot
        mobile_context = await browser.new_context(viewport={'width': 390, 'height': 844}, user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1")
        mobile_page = await mobile_context.new_page()
        
        # We need to transfer cookies or login again. Transferring cookies:
        cookies = await context.cookies()
        await mobile_context.add_cookies(cookies)
        
        await mobile_page.goto("http://127.0.0.1:8000/console/")
        await mobile_page.wait_for_load_state("networkidle")
        
        await mobile_page.evaluate("""
            if (document.getElementById('djDebug')) document.getElementById('djDebug').style.display = 'none';
        """)
        
        print("Taking mobile screenshot...")
        await mobile_page.screenshot(path="static/img/mobile_dashboard.png")
        
        await browser.close()
        print("Screenshots captured successfully!")

if __name__ == "__main__":
    asyncio.run(main())
