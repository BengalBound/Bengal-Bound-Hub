"""
Smoke-test every AI agent dashboard.
Run: .venv/Scripts/python scripts/test_agents_ui.py
"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'bengalbound_core.settings.development'

from playwright.sync_api import sync_playwright

BASE = "http://localhost:1234"
EMAIL = "playwright@bengalbound.com"
PASSWORD = "TestPass123!"
SLUG = "test-business"

AGENTS = [
    "aria","atlas","babel","cash","clarity","concierge","content-architect",
    "crux","dox","flux","hera","kai","lead-hunter","luma","medibook","merch",
    "mira","nexus","nova","oracle","payload","pulse","realt","reporting-bot",
    "sage","scout","serea-content","shield","tempo","voice-receptionist",
]

results = {}

def login(page):
    page.goto(f"{BASE}/accounts/login/")
    page.fill('input[name="login"]', EMAIL)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle", timeout=10000)
    # Skip email confirmation if redirected there
    if "confirm-email" in page.url or "email" in page.url:
        page.goto(f"{BASE}/hub/{SLUG}/")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

def test_agent(page, slug):
    url = f"{BASE}/hub/{SLUG}/agents/{slug}/"
    page.goto(url, timeout=15000)
    page.wait_for_load_state("domcontentloaded", timeout=10000)

    status = page.evaluate("() => document.readyState")
    http_ok  = "404" not in page.title() and "500" not in page.title() and "error" not in page.title().lower()

    # Count interactive elements
    buttons  = page.locator("button, input[type='submit'], a.btn").count()
    forms    = page.locator("form").count()
    errors   = page.locator(".alert-danger, .errorlist, [class*='error']").count()

    # Check for JS console errors
    js_errors = []
    page.on("pageerror", lambda e: js_errors.append(str(e)))

    # Try clicking the first non-dangerous button (not delete/logout)
    first_btn = page.locator(
        "button:not([data-confirm]):not([class*='delete']):not([class*='logout']), "
        "input[type='submit']:not([value*='Delete'])"
    ).first
    btn_clicked = False
    btn_text = ""
    if first_btn.count() > 0:
        try:
            btn_text = first_btn.inner_text().strip()[:30]
            first_btn.click(timeout=3000)
            page.wait_for_load_state("domcontentloaded", timeout=5000)
            btn_clicked = True
        except Exception:
            pass

    return {
        "url": url,
        "title": page.title()[:60],
        "http_ok": http_ok,
        "buttons": buttons,
        "forms": forms,
        "page_errors": errors,
        "btn_clicked": btn_clicked,
        "btn_text": btn_text,
    }

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()

    print("Logging in...")
    login(page)
    print(f"Logged in — current URL: {page.url}\n")

    print(f"{'Agent':<22} {'HTTP':>4}  {'Btns':>4}  {'Forms':>5}  {'Errs':>4}  {'Btn clicked'}")
    print("-" * 72)

    ok_count = fail_count = 0

    for slug in AGENTS:
        try:
            r = test_agent(page, slug)
            icon = "OK" if r["http_ok"] and r["page_errors"] == 0 else "!!"
            if r["http_ok"] and r["page_errors"] == 0:
                ok_count += 1
            else:
                fail_count += 1
            clicked_info = f"'{r['btn_text']}'" if r["btn_clicked"] else "—"
            print(f"[{icon}] {slug:<22} {'OK' if r['http_ok'] else 'FAIL':>4}  {r['buttons']:>4}  {r['forms']:>5}  {r['page_errors']:>4}  {clicked_info}")
            results[slug] = r
        except Exception as e:
            fail_count += 1
            print(f"[!!] {slug:<22} CRASH: {e}")
            results[slug] = {"http_ok": False, "error": str(e)}

    print("-" * 72)
    print(f"\nSummary: {ok_count} passed, {fail_count} failed out of {len(AGENTS)} agents\n")

    # Print failures in detail
    failures = {k:v for k,v in results.items() if not v.get("http_ok", False) or v.get("page_errors", 0) > 0}
    if failures:
        print("=== FAILURES / ISSUES ===")
        for slug, r in failures.items():
            print(f"\n  {slug}:")
            print(f"    URL:    {r.get('url','?')}")
            print(f"    Title:  {r.get('title','?')}")
            print(f"    Error:  {r.get('error', 'page errors: '+str(r.get('page_errors',0)))}")
    else:
        print("All agents loaded with no errors!")

    browser.close()
