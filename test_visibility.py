import time
import subprocess
import os
from playwright.sync_api import sync_playwright

def run_visibility_test():
    print("Starting Django dev server...")
    server = subprocess.Popen(
        [".venv\\Scripts\\python.exe", "manage.py", "runserver", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(5)  # wait for server to start

    artifact_dir = r"C:\Users\shadm\.gemini\antigravity-ide\brain\238ab3a1-140d-4912-9a46-2624fae823f9"
    urls = [
        ("restaurants", "http://127.0.0.1:8000/solutions/restaurants/"),
        ("retail", "http://127.0.0.1:8000/solutions/retail-ecommerce/"),
        ("hospitality", "http://127.0.0.1:8000/solutions/hospitality-rentals/"),
        ("home", "http://127.0.0.1:8000/")
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 800})

            for name, url in urls:
                print(f"Testing {name}...")
                page.goto(url)
                time.sleep(2)
                try:
                    page.evaluate('document.getElementById("djDebug").style.display="none";')
                except Exception:
                    pass
                screenshot_path = os.path.join(artifact_dir, f"visibility_{name}.png")
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"Saved {screenshot_path}")

            browser.close()
    finally:
        print("Stopping server...")
        server.terminate()
        server.wait()

if __name__ == "__main__":
    run_visibility_test()
