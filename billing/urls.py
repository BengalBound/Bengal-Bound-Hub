from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('checkout/<str:plan_type>/', views.checkout_redirect, name='checkout'),
    path('stripe/initiate/<str:plan_type>/', views.stripe_initiate, name='stripe_initiate'),
    path('portal/', views.portal_redirect, name='portal'),
    path('webhook/', views.stripe_webhook, name='webhook'),
    
    # bKash Checkouts
    path('bkash/initiate/<str:plan_type>/', views.bkash_initiate, name='bkash_initiate'),
    path('bkash/callback/', views.bkash_callback, name='bkash_callback'),
    path('bkash/cancel/', views.bkash_cancel, name='bkash_cancel'),
    
    path('success/', views.success_view, name='success'),
    path('cancel/', views.cancel_view, name='cancel'),
]
