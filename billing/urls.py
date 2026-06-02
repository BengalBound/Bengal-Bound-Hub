from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('checkout/<str:plan_type>/', views.checkout_redirect, name='checkout'),
    path('portal/', views.portal_redirect, name='portal'),
    path('webhook/', views.stripe_webhook, name='webhook'),
    path('success/', views.success_view, name='success'),
    path('cancel/', views.cancel_view, name='cancel'),
]
