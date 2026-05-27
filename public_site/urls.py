from django.urls import path, include
from . import views

app_name = 'public_site'

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('products/', views.products, name='products'),
    path('pricing/', views.pricing, name='pricing'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('contact/', views.contact, name='contact'),
    path('consult/', views.consult, name='consult'),
    # Phase 4 additions
    path('hire-ai/', views.ai_job_portal, name='ai_job_portal'),
    path('affiliates/', views.affiliate_portal, name='affiliate_portal'),
    path('trial/', views.trial_request, name='trial_request'),
    # SSO consume endpoint for public site
    path('accounts/sso/consume/', views.sso_consume_proxy, name='sso_consume'),
]
