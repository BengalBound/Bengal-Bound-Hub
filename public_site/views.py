from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth import login, get_user_model
from .models import (
    Service, Product, BlogPost, ContactInquiry, HomepageContent, Partner, VideoRepresentation, VideoReview, FAQ,
    TrialAccount, CoreValue, PlatformFeature, WorkProcessStep, Testimonial,
    Documentation, DocumentationCategory
)
from workspace_admin.models import AIEmployeeTier

EXCHANGE_RATES = {
    'USD': 1.0,
    'EUR': 0.92,
    'GBP': 0.79,
    'BDT': 110.0,
    'INR': 83.0
}
CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'BDT': '৳',
    'INR': '₹'
}

def set_currency(request):
    currency = request.GET.get('currency', 'USD')
    if currency in EXCHANGE_RATES:
        request.session['currency'] = currency
    return redirect(request.META.get('HTTP_REFERER', '/'))


def home(request):
    hero_content = HomepageContent.objects.first()
    partners = Partner.objects.all()
    videos = VideoRepresentation.objects.filter(is_active=True)
    reviews = VideoReview.objects.filter(is_featured=True)
    faqs = FAQ.objects.filter(is_active=True)
    services = Service.objects.filter(is_active=True)[:6]

    core_values = CoreValue.objects.filter(is_active=True)
    platform_features = PlatformFeature.objects.filter(is_active=True)
    work_process_steps = WorkProcessStep.objects.filter(is_active=True)
    testimonials = Testimonial.objects.filter(is_featured=True)

    # Showcase the subscription-based AI roles
    ai_tiers = AIEmployeeTier.objects.all().order_by('token_limit')

    docs = Documentation.objects.filter(is_active=True)
    doc_categories = DocumentationCategory.objects.all()

    currency = request.session.get('currency', 'USD')
    rate = EXCHANGE_RATES.get(currency, 1.0)
    symbol = CURRENCY_SYMBOLS.get(currency, '$')
    
    from decimal import Decimal
    decimal_rate = Decimal(str(rate))
    for tier in ai_tiers:
        tier.local_monthly_price = int(tier.monthly_price_usd * decimal_rate)

    context = {
        'hero_content': hero_content,
        'partners': partners,
        'videos': videos,
        'reviews': reviews,
        'faqs': faqs,
        'services': services,
        'core_values': core_values,
        'platform_features': platform_features,
        'work_process_steps': work_process_steps,
        'testimonials': testimonials,
        'ai_tiers': ai_tiers,
        'docs': docs,
        'doc_categories': doc_categories,
        'currency': currency,
        'exchange_rate': rate,
        'currency_symbol': symbol,
    }
    return render(request, 'public_site/home.html', context)

def about(request):
    return render(request, 'public_site/about.html')

def services(request):
    services = Service.objects.filter(is_active=True)
    return render(request, 'public_site/services.html', {'services': services})

def products(request):
    products = Product.objects.filter(is_active=True)
    return render(request, 'public_site/products.html', {'products': products})

def pricing(request):
    from hub.models import HubPlanConfig, INDUSTRY_MODULE_PRIORITY
    plans = HubPlanConfig.objects.filter(is_visible=True).order_by('monthly_price_usd')
    # Seed defaults if DB is empty
    if not plans.exists():
        from hub.views import _seed_plan_defaults
        _seed_plan_defaults()
        plans = HubPlanConfig.objects.filter(is_visible=True).order_by('monthly_price_usd')
        
    currency = request.session.get('currency', 'USD')
    rate = EXCHANGE_RATES.get(currency, 1.0)
    symbol = CURRENCY_SYMBOLS.get(currency, '$')
    
    from decimal import Decimal
    decimal_rate = Decimal(str(rate))
    for plan in plans:
        plan.local_monthly_price = int(plan.monthly_price_usd * decimal_rate)
        plan.local_ip_addon = int(plan.ip_locked_addon_usd * decimal_rate)
        plan.local_self_addon = int(plan.self_hosted_addon_usd * decimal_rate)

    local_pro_min = int(99 * decimal_rate)
    local_pro_max = int(999 * decimal_rate)

    return render(request, 'public_site/pricing.html', {
        'plans': plans,
        'industry_map': INDUSTRY_MODULE_PRIORITY,
        'currency': currency,
        'exchange_rate': rate,
        'currency_symbol': symbol,
        'local_pro_min': local_pro_min,
        'local_pro_max': local_pro_max,
    })

def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'public_site/blog_list.html', {'posts': posts})

def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, 'public_site/blog_detail.html', {'post': post})

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        ContactInquiry.objects.create(
            name=name, email=email, subject=subject, message=message
        )
        messages.success(request, "Your message has been sent successfully!")
        return redirect('public_site:contact')

    from .models import CompanyDetails
    company = CompanyDetails.objects.first()
    return render(request, 'public_site/contact.html', {'company': company})

def consult(request):
    if request.method == 'POST':
        from booking_calendar.models import Appointment
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        service_type = request.POST.get('service_type', 'custom_website')
        date = request.POST.get('preferred_date')
        time = request.POST.get('preferred_time')
        notes = request.POST.get('notes', '')

        Appointment.objects.create(
            client_name=name, client_email=email, client_phone=phone,
            service_type=service_type, date=date, time=time, notes=notes
        )
        messages.success(request, "Your appointment request has been scheduled! We will contact you soon.")
        return redirect('public_site:consult')

    return render(request, 'public_site/consult.html')

def ai_job_portal(request):
    """
    AI Job Portal — Searchable directory where clients can browse AI employees
    by industry (role) and seniority (tier level).
    """
    from agents.models import AgentCatalog
    agents = AgentCatalog.objects.filter(is_active=True).order_by('category', 'name')
    tiers = AIEmployeeTier.objects.all()
    tier_map = {t.name: t for t in tiers}

    # Search/filter params
    search_role = request.GET.get('role', '')
    search_level = request.GET.get('level', '')

    if search_role:
        agents = agents.filter(category=search_role)
    if search_level:
        agents = agents.filter(tier_required=search_level)

    # Attach tier data dynamically for the template
    currency = request.session.get('currency', 'USD')
    rate = EXCHANGE_RATES.get(currency, 1.0)
    symbol = CURRENCY_SYMBOLS.get(currency, '$')
    from decimal import Decimal
    decimal_rate = Decimal(str(rate))

    for agent in agents:
        agent.tier_obj = tier_map.get(agent.tier_required)
        if agent.tier_obj:
            agent.local_monthly_price = int(agent.tier_obj.monthly_price_usd * decimal_rate)
        else:
            agent.local_monthly_price = 0

    return render(request, 'public_site/ai_job_portal.html', {
        'agents': agents,
        'role_choices': [(c, c) for c in AgentCatalog.objects.values_list('category', flat=True).distinct().order_by('category')],
        'level_choices': AIEmployeeTier.TIERS,
        'search_role': search_role,
        'search_level': search_level,
        'currency': currency,
        'currency_symbol': symbol,
    })

def affiliate_portal(request):
    """
    Public-facing Affiliate Portal landing page.
    Authenticated console users with the 'affiliate' role can see their link.
    Others see a sign-up prompt.
    """
    affiliate_profile = None
    if request.user.is_authenticated and request.user.role == 'affiliate':
        affiliate_profile = getattr(request.user, 'affiliate_profile', None)

    return render(request, 'public_site/affiliate_portal.html', {
        'affiliate_profile': affiliate_profile,
    })

def trial_request(request):
    """
    Trial Account request form. Workspace Admin reviews and approves.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        company_name = request.POST.get('company_name', '')
        use_case = request.POST.get('use_case', '')

        if TrialAccount.objects.filter(email=email).exists():
            messages.warning(request, "A trial request for this email already exists.")
        else:
            TrialAccount.objects.create(
                name=name, email=email,
                company_name=company_name, use_case=use_case
            )
            messages.success(request, "Your trial request has been submitted! We will contact you shortly.")
        return redirect('trial_request')

    return render(request, 'public_site/trial_request.html')

def sso_consume_proxy(request):
    """Receives an SSO token on the public-site domain, verifies it, and logs the user in."""
    token = request.GET.get('sso_token')
    next_url = request.GET.get('next', '/')
    if token:
        User = get_user_model()
        signer = TimestampSigner()
        try:
            user_id = signer.unsign(token, max_age=30)
            user = User.objects.filter(id=user_id).first()
            if user:
                login(request, user)
        except (BadSignature, SignatureExpired):
            pass
    return redirect(next_url)

def ai_superiority_showcase(request):
    """
    Dedicated landing page explaining BengalBound's AI architecture,
    specifically the Human-in-the-Loop safeguard system.
    """
    return render(request, 'public_site/why_us.html')

def docs_list(request):
    docs = Documentation.objects.filter(is_active=True)
    doc_categories = DocumentationCategory.objects.all()
    return render(request, 'public_site/docs_list.html', {
        'docs': docs,
        'doc_categories': doc_categories,
    })

def privacy(request):
    return render(request, 'public_site/privacy.html')

def terms(request):
    return render(request, 'public_site/terms.html')
