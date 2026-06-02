import os

replacements = [
    (r"d:\Bengal bound\dev-backoffice\docs\dev\DEV_KIT.md", "### Public Site (Cloud Run):\n*   Export: `python manage.py export_static --settings=netlify_settings`\n*   Output: `netlify_dist/`\n*   Config: ``", "### Public Site (Cloud Run):\n*   Served directly via Django templates."),
    (r"d:\Bengal bound\dev-backoffice\docs\cto\CTO_BRIEFING.md", "Public site templates (`templates/public_site/`) exported to `netlify_dist/`:\n\n```bash\npython manage.py export_static --settings=netlify_settings\n```\n\nConfig: ``. Settings: ``.", "Public site templates (`templates/public_site/`) are served directly by Cloud Run."),
    (r"d:\Bengal bound\dev-backoffice\docs\tech\DEPLOYMENT_GUIDE.md", "1. Sign up at **netlify.com**", "1. Connect custom domain in Cloud Run dashboard"),
    (r"d:\Bengal bound\dev-backoffice\docs\tech\DEPLOYMENT_GUIDE.md", "6. Public site live at `https://your-site.netlify.app`", "6. Public site live at `https://your-site.com`"),
    (r"d:\Bengal bound\dev-backoffice\docs\tech\DEPLOYMENT_GUIDE.md", "CNAME  @        your-site.netlify.app       (public site)\n   CNAME  app      bengalbound-hub-*.run.app (backend)\n   CNAME  www      your-site.netlify.app", "A      @        <cloud-run-ip>       (public site)\n   CNAME  app      bengalbound-hub-*.run.app (backend)\n   CNAME  www      ghs.googlehosted.com"),
    (r"d:\Bengal bound\dev-backoffice\docs\testing\LAUNCH_CHECKLIST.md", "python manage.py export_static --settings=netlify_settings", "python manage.py collectstatic"),
    (r"d:\Bengal bound\dev-backoffice\templates\public_site\privacy.html", '<li><strong class="text-white">Netlify</strong> — static site hosting (US CDN)</li>', '<li><strong class="text-white">Google Cloud Run</strong> — managed application hosting (US CDN)</li>'),
    (r"d:\Bengal bound\dev-backoffice\docs\architecture\SYSTEM_ARCHITECTURE.md", "- Public site: Cloud Run (``, export via `python manage.py export_static --settings=netlify_settings`)", "- Public site: Cloud Run (served via Django templates)"),
    (r"d:\Bengal bound\dev-backoffice\docs\architecture\SYSTEM_ARCHITECTURE.md", "              │     └── python manage.py export_static --settings=netlify_settings", "              │     └── python manage.py collectstatic"),
    (r"d:\Bengal bound\dev-backoffice\bengalbound_core\settings\production.py", "    'https://*.netlify.app',       # Netlify preview\n", ""),
    (r"d:\Bengal bound\dev-backoffice\bengalbound_core\settings\production.py", "    'https://*.onrender.com',      # Render\n", ""),
]

for filepath, old, new in replacements:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if old in content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content.replace(old, new))
            print(f"Cleaned {filepath}")
        else:
            print(f"Target string not found in {filepath}")
