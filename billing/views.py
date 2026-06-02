import stripe
import json
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .services import create_checkout_session, create_portal_session
from .models import BillingEvent
from hub.models import BusinessInstance, BusinessSubscription

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def checkout_redirect(request, plan_type):
    # Determine the business context. For now, we assume the user owns exactly one business instance for simplicity.
    business = BusinessInstance.objects.filter(owner=request.user).first()
    if not business:
        return HttpResponse("No business instance found.", status=404)
        
    billing_cycle = request.GET.get('cycle', 'monthly')
    base_url = request.build_absolute_uri('/')[:-1]
    
    try:
        url = create_checkout_session(business, plan_type, billing_cycle, base_url)
        return redirect(url)
    except Exception as e:
        return HttpResponse(str(e), status=400)

@login_required
def portal_redirect(request):
    business = BusinessInstance.objects.filter(owner=request.user).first()
    if not business:
        return HttpResponse("No business instance found.", status=404)
        
    base_url = request.build_absolute_uri('/')[:-1]
    
    try:
        url = create_portal_session(business, base_url)
        return redirect(url)
    except Exception as e:
        return HttpResponse(str(e), status=400)

def success_view(request):
    return HttpResponse("Payment successful! Your subscription is now active.")

def cancel_view(request):
    return HttpResponse("Payment cancelled.")

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    # Log event
    BillingEvent.objects.create(
        stripe_customer_id=event.data.object.get('customer'),
        event_id=event.id,
        event_type=event.type,
        payload=event.data.object
    )

    # Handle event
    if event.type == 'checkout.session.completed':
        session = event.data.object
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        client_reference_id = session.get('client_reference_id')

        if client_reference_id and subscription_id:
            try:
                business = BusinessInstance.objects.get(id=client_reference_id)
                # Ensure the subscription has this customer
                sub, created = BusinessSubscription.objects.get_or_create(business=business)
                
                # Fetch sub to get price ID
                stripe_sub = stripe.Subscription.retrieve(subscription_id)
                price_id = stripe_sub.items.data[0].price.id
                
                sub.stripe_subscription_id = subscription_id
                sub.stripe_price_id = price_id
                sub.status = 'active'
                
                # Extract plan info from metadata if passed in checkout session
                metadata = session.get('metadata', {})
                if metadata.get('plan_type'):
                    sub.plan_type = metadata.get('plan_type')
                if metadata.get('billing_cycle'):
                    sub.billing_cycle = metadata.get('billing_cycle')
                
                sub.save()
            except BusinessInstance.DoesNotExist:
                pass

    elif event.type in ['customer.subscription.updated', 'customer.subscription.deleted']:
        subscription = event.data.object
        customer_id = subscription.get('customer')
        sub_id = subscription.get('id')
        status = subscription.get('status')
        
        try:
            sub = BusinessSubscription.objects.get(stripe_subscription_id=sub_id)
            if status == 'active':
                sub.status = 'active'
            elif status == 'canceled' or status == 'incomplete_expired':
                sub.status = 'cancelled'
            elif status == 'past_due' or status == 'unpaid':
                sub.status = 'pending'
            
            # Update price if plan changed
            price_id = subscription.items.data[0].price.id
            sub.stripe_price_id = price_id
            
            sub.save()
        except BusinessSubscription.DoesNotExist:
            pass

    return HttpResponse(status=200)
