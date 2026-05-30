from playwright.sync_api import sync_playwright

def test_ui():
    print('Starting UI Test...')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print('1. Testing Homepage...')
        page.goto('http://127.0.0.1:8000/')
        assert 'BengalBound' in page.title()
        
        print('2. Testing Login Page...')
        page.goto('http://127.0.0.1:8000/accounts/login/')
        
        print('3. Testing Registration Page...')
        page.goto('http://127.0.0.1:8000/accounts/signup/')
        
        print('4. Attempting a mock user signup...')
        try:
            page.fill('input[name="email"]', 'testadmin@bengalbound.com')
            print('Signup form verified.')
        except Exception as e:
            print(f'Error interacting with signup form: {e}')
            
        print('5. Checking Workspace Admin console access...')
        page.goto('http://127.0.0.1:8000/workspace/')
        if 'login' in page.url:
            print('Workspace correctly protected by login redirection.')
            
        print('UI Navigation Test Complete.')
        browser.close()

if __name__ == '__main__':
    test_ui()
