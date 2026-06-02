import os

replacements = {
    "Render (free tier)": "Cloud Run",
    "Render dashboard": "Cloud Run dashboard",
    "Render": "Cloud Run",
    "Netlify": "Cloud Run",
    "netlify.toml": "",
    "netlify_settings.py": "",
    "bengalbound-web.onrender.com": "bengalbound-hub-*.run.app"
}

def process_file(filepath):
    if not filepath.endswith('.md'):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for old, new in replacements.items():
        if old in new_content:
            new_content = new_content.replace(old, new)
            
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, _, files in os.walk(r"d:\Bengal bound\dev-backoffice\docs"):
    for file in files:
        process_file(os.path.join(root, file))
