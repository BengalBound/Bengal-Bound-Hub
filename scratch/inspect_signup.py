import time
from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://127.0.0.1:1234/accounts/signup/")
        time.sleep(2)
        
        # Check computed styles of all .glass-card elements
        styles = page.evaluate('''() => {
            const cards = Array.from(document.querySelectorAll('.glass-card'));
            return cards.map(el => {
                const comp = window.getComputedStyle(el);
                return {
                    parent: el.parentElement.className,
                    className: el.className,
                    background: comp.background,
                    backdropFilter: comp.backdropFilter || comp.webkitBackdropFilter,
                    border: comp.border,
                    borderRadius: comp.borderRadius,
                    boxShadow: comp.boxShadow,
                    display: comp.display
                };
            });
        }''')
        for i, s in enumerate(styles):
            print(f"Card {i}:", s)
        browser.close()

if __name__ == "__main__":
    inspect()
