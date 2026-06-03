from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_redirect_view, name='signup_redirect'),
    path('register/', views.register_view, name='register'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),

    # Custom login handles subdomain-aware redirect
    path('login/', views.custom_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # Cross-subdomain SSO
    path('sso/redirect/', views.sso_redirect_view, name='sso_redirect'),
    path('sso/consume/', views.sso_consume_view, name='sso_consume'),

    # Two-Factor Authentication
    path('2fa/setup/', views.totp_setup_view, name='totp_setup'),
    path('2fa/challenge/', views.totp_challenge_view, name='totp_challenge'),
]
