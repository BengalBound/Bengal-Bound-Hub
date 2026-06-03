import time
import subprocess
import os
from playwright.sync_api import sync_playwright

def run_visibility_test():
    print("Starting Django dev server...")
    server = subprocess.Popen(
        [".venv\\Scripts\\python.exe", "manage.py", "runserver", "1234"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(5)  # wait for server to start

    artifact_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visibility_results')
    os.makedirs(artifact_dir, exist_ok=True)
    urls = [
        ("restaurants", "http://127.0.0.1:1234/solutions/restaurants/"),
        ("retail", "http://127.0.0.1:1234/solutions/retail-ecommerce/"),
        ("hospitality", "http://127.0.0.1:1234/solutions/hospitality-rentals/"),
        ("home", "http://127.0.0.1:1234/")
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
