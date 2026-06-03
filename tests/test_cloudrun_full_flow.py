"""
End-to-End full flow test targeting the live Cloud Run deployment.
Run via: .venv/Scripts/python -m pytest tests/test_cloudrun_full_flow.py
"""
import os
import pytest
from playwright.sync_api import sync_playwright, expect

# Set the base URL for the Cloud Run deployment
BASE_URL = os.environ.get("CLOUDRUN_URL", "https://bengal-bound-hub-u5i67kezxa-vp.a.run.app")

# We skip this test in normal CI unless explicitly requested or if targeting Cloud Run
@pytest.mark.skipif(not os.environ.get("RUN_CLOUDRUN_TESTS"), reason="Only run when testing live deployment")
def test_cloud_run_end_to_end_flow():
    """
    Simulates the full flow on the deployed Cloud Run instance:
    1. Loads the homepage.
    2. Navigates to Login.
    3. (Optional) In a real scenario, logs in with a test account.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Load the homepage
        print(f"Navigating to {BASE_URL}...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Verify it loads without 500 errors
        assert "500" not in page.title()
        assert "404" not in page.title()

        # 2. Navigate to Login page
        print("Navigating to /accounts/login/ ...")
        page.goto(f"{BASE_URL}/accounts/login/")
        page.wait_for_load_state("networkidle")
        
        # Check for login form elements
        login_input = page.locator('input[name="username"]')
        password_input = page.locator('input[name="password"]')
        
        expect(login_input).to_be_visible()
        expect(password_input).to_be_visible()
        
        print("Login page loaded successfully on Cloud Run.")

        browser.close()

if __name__ == "__main__":
    # If run directly as a script, execute the flow without pytest markers
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        print("--- Starting Full Flow Test on Cloud Run ---")
        print(f"Target: {BASE_URL}")

        try:
            page.goto(BASE_URL, timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            print(f"Homepage Title: {page.title()}")
            
            page.goto(f"{BASE_URL}/accounts/login/", timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            
            # Find forms
            form_count = page.locator("form").count()
            print(f"Found {form_count} forms on the login page.")
            
            if form_count > 0:
                print("Login Flow UI is functioning on Cloud Run deployment.")
            else:
                print("Error: Could not locate login form.")
                
        except Exception as e:
            print(f"Cloud Run Flow Test failed: {e}")
            
        finally:
            browser.close()
            print("--- Flow Test Complete ---")
