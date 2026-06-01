import os
import django

if 'K_SERVICE' in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bengalbound_core.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bengalbound_core.settings.development')
django.setup()

from public_site.models import (
    CompanyDetails, FAQ, CoreValue, PlatformFeature, WorkProcessStep, 
    DocumentationCategory, Documentation, BlogCategory, BlogPost, HomepageContent,
    VideoRepresentation, Service
)
from django.contrib.auth import get_user_model

def seed_db():
    User = get_user_model()
    admin = User.objects.filter(is_superuser=True).first()
    print("Seeding CompanyDetails...")
    CompanyDetails.objects.get_or_create(id=1, defaults={
        'address': '123 AI Boulevard\nTech District, Innovation City 90210',
        'phone': '+1 (800) 555-0199',
        'email': 'hello@bengalbound.com',
        'working_hours': 'Mon - Fri, 9am - 6pm EST'
    })

    print("Seeding HomepageContent...")
    HomepageContent.objects.get_or_create(id=1, defaults={
        'hero_title1': 'Next-Gen Workforces.',
        'hero_title2': 'Automated & Unbound.',
        'hero_subtitle': 'BengalBound provides enterprise-grade Workspace as a Service (WaaS) paired with fully autonomous AI Agents that run your business on autopilot.',
        'primary_button_text': 'Book Your Demo',
        'primary_button_url': '/consult/',
        'secondary_button_text': 'Explore AI Agents',
        'secondary_button_url': '/hire-ai/'
    })

    print("Seeding FAQs...")
    faqs = [
        ("What is Bengal Bound?", "Bengal Bound is an enterprise platform combining Workspace as a Service (WaaS) with highly trained, role-specific AI Employees. We deploy entire backoffice systems tailored to your industry."),
        ("How do the AI Employees work?", "Our AI agents integrate directly into your workflow. Whether it's a customer support agent reading emails and drafting replies, or a sales analyst generating reports, they operate within our secure ecosystem 24/7."),
        ("Can I host this on my own servers?", "Yes! While our Cloud Hosted plans are highly secure, we also offer IP-Locked environments and fully Self-Hosted dedicated server deployments for maximum privacy."),
        ("Do I need technical skills to use this?", "Not at all. We handle the entire deployment, training of the AI agents, and integration of the CRM/ERP systems. You simply log into your custom dashboard and start managing.")
    ]
    for i, (q, a) in enumerate(faqs):
        FAQ.objects.get_or_create(question=q, defaults={'answer': a, 'order': i})

    print("Seeding CoreValues...")
    cvs = [
        ("Built for Scale", "Architected for high concurrency and zero downtime. Your operations grow without technical bottlenecks.", "bi-rocket-takeoff"),
        ("Bank-Grade Security", "End-to-end encryption, regular audits, and robust Role Based Access Control ensure your data is locked down tight.", "bi-shield-check")
    ]
    for i, (t, d, ic) in enumerate(cvs):
        CoreValue.objects.get_or_create(title=t, defaults={'description': d, 'icon_class': ic, 'order': i})

    print("Seeding PlatformFeatures...")
    pfs = [
        ("Smart Integrations", "Connect directly with Stripe, OpenAI, Slack, and 50+ other leading platforms instantly.", "bi-plug"),
        ("Custom AI Training", "We train agents on your specific business documentation for hyper-accurate responses.", "bi-robot")
    ]
    for i, (t, d, ic) in enumerate(pfs):
        PlatformFeature.objects.get_or_create(title=t, defaults={'description': d, 'icon_class': ic, 'order': i})

    print("Seeding WorkProcessSteps...")
    wps = [
        ("Discovery Call", "We analyze your bottlenecks and identify exactly where automation and WaaS will save you time and money.", "bi-search"),
        ("Custom Deployment", "Our engineers deploy a tailored environment with pre-trained AI agents mapped to your workflows.", "bi-cloud-upload"),
        ("Go Live & Scale", "You take the keys. Your human team focuses on strategy while our agents handle the repetitive execution.", "bi-graph-up-arrow")
    ]
    for i, (t, d, ic) in enumerate(wps):
        WorkProcessStep.objects.get_or_create(title=t, defaults={'description': d, 'step_number': i+1, 'icon_class': ic})

    print("Seeding Blog & Docs...")
    bc, _ = BlogCategory.objects.get_or_create(name='AI Trends', slug='ai-trends')
    BlogPost.objects.get_or_create(title='The Future of AI Employees', slug='future-of-ai', defaults={
        'author': admin, 'category': bc, 'is_published': True,
        'content': '<p>AI Employees are no longer science fiction. By 2030, businesses that haven\'t adopted autonomous agent architectures will struggle to compete. Here is how Bengal Bound is leading the charge...</p>'
    })

    dc, _ = DocumentationCategory.objects.get_or_create(name='Getting Started', slug='getting-started')
    Documentation.objects.get_or_create(title='Platform Overview Tutorial', slug='platform-overview', defaults={
        'excerpt': 'Learn how to navigate your newly deployed Workspace ecosystem and manage your first AI Employee.',
        'category': dc, 'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'is_active': True, 'author_name': 'Support Team'
    })
    
    print("Seeding VideoRepresentation...")
    VideoRepresentation.objects.get_or_create(title='See Bengal Bound in Action', defaults={
        'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'description': 'Watch a 2-minute demonstration of how our ecosystem unified 4 disparate tools into one cohesive, AI-powered platform.',
        'is_active': True
    })

    print("Seeding Services...")
    services = [
        ("AI Operations Manager", "Automate workflows and coordinate team operations round the clock.", "bi-robot"),
        ("Data Analyst Agent", "Instantly transform raw data into actionable dashboards and insights.", "bi-bar-chart-fill"),
        ("Customer Support Bot", "Handle customer inquiries with human-like empathy 24/7.", "bi-headset"),
        ("Sales Outreach AI", "Personalize outreach and nurture leads automatically.", "bi-envelope-paper-heart"),
        ("Financial Auditor", "Monitor transactions and flag anomalies in real time.", "bi-bank"),
        ("Marketing Content Gen", "Draft blogs, social media posts, and ad copy at scale.", "bi-pen")
    ]
    for i, (t, d, ic) in enumerate(services):
        Service.objects.get_or_create(slug=t.lower().replace(' ', '-'), defaults={'title': t, 'description': d, 'icon_class': ic})

    print("Done!")

if __name__ == '__main__':
    seed_db()
