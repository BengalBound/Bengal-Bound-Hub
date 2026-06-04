import stripe
import json
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .services import create_checkout_session, create_portal_session
from .bkash_service import BKashService
from .models import BillingEvent
from hub.models import BusinessInstance, BusinessSubscription, HubPlanConfig
import uuid

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def checkout_redirect(request, plan_type):
    business_id = request.GET.get('business_id')
    if business_id:
        from django.shortcuts import get_object_or_404
        business = get_object_or_404(BusinessInstance, id=business_id, owner=request.user)
    else:
        business = BusinessInstance.objects.filter(owner=request.user).first()

    if not business:
        return HttpResponse("No business instance found.", status=404)
        
    billing_cycle = request.GET.get('cycle', 'monthly')
    
    # Render the checkout selection page
    return render(request, 'billing/checkout.html', {
        'business': business,
        'plan_type': plan_type,
        'billing_cycle': billing_cycle,
    })

@login_required
def stripe_initiate(request, plan_type):
    business_id = request.GET.get('business_id')
    if business_id:
        from django.shortcuts import get_object_or_404
        business = get_object_or_404(BusinessInstance, id=business_id, owner=request.user)
    else:
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
    business_id = request.GET.get('business_id')
    if business_id:
        from django.shortcuts import get_object_or_404
        business = get_object_or_404(BusinessInstance, id=business_id, owner=request.user)
    else:
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
    business_id = request.GET.get('business_id')
    business = None
    sub = None
    if business_id:
        try:
            business = BusinessInstance.objects.get(id=business_id)
            sub = getattr(business, 'subscription', None)
        except BusinessInstance.DoesNotExist:
            pass
            
    # Fallback context sidebar variables
    user_businesses = []
    if request.user.is_authenticated:
        user_businesses = BusinessInstance.objects.filter(owner=request.user)

    return render(request, 'billing/success.html', {
        'biz': business,
        'current_business': business,
        'sub': sub,
        'user_businesses': user_businesses,
        'hub_is_owner': business.owner == request.user if business else False,
    })

def cancel_view(request):
    business_id = request.GET.get('business_id')
    business = None
    if business_id:
        try:
            business = BusinessInstance.objects.get(id=business_id)
        except BusinessInstance.DoesNotExist:
            pass

    # Fallback context sidebar variables
    user_businesses = []
    if request.user.is_authenticated:
        user_businesses = BusinessInstance.objects.filter(owner=request.user)

    return render(request, 'billing/cancel.html', {
        'biz': business,
        'current_business': business,
        'user_businesses': user_businesses,
        'hub_is_owner': business.owner == request.user if business else False,
    })

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
    try:
        payload_dict = json.loads(payload)
        event_obj = payload_dict.get('data', {}).get('object', {})
    except Exception:
        event_obj = {}

    BillingEvent.objects.create(
        stripe_customer_id=getattr(event.data.object, 'customer', None),
        event_id=event.id,
        event_type=event.type,
        payload=event_obj
    )

    # Handle event
    if event.type == 'checkout.session.completed':
        session = event.data.object
        customer_id = getattr(session, 'customer', None)
        subscription_id = getattr(session, 'subscription', None)
        client_reference_id = getattr(session, 'client_reference_id', None)

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
                metadata = getattr(session, 'metadata', {}) or {}
                plan_type = metadata.get('plan_type') if hasattr(metadata, 'get') else getattr(metadata, 'plan_type', None)
                billing_cycle = metadata.get('billing_cycle') if hasattr(metadata, 'get') else getattr(metadata, 'billing_cycle', None)
                if plan_type:
                    sub.plan_type = plan_type
                if billing_cycle:
                    sub.billing_cycle = billing_cycle
                
                sub.save()

                try:
                    from bengalbound_core.notifications import send_slack_alert
                    send_slack_alert(
                        title="💰 New Subscription (Stripe) 💰",
                        message=f"Business: {business.name} ({business.slug})\nPlan: {plan_type} ({billing_cycle})",
                        urgency="high"
                    )
                except Exception as e:
                    pass
            except BusinessInstance.DoesNotExist:
                pass

    elif event.type in ['customer.subscription.updated', 'customer.subscription.deleted']:
        subscription = event.data.object
        customer_id = getattr(subscription, 'customer', None)
        sub_id = getattr(subscription, 'id', None)
        status = getattr(subscription, 'status', None)
        if event.type == 'customer.subscription.deleted':
            status = 'canceled'
        
        try:
            sub = BusinessSubscription.objects.get(stripe_subscription_id=sub_id)
            if status == 'active':
                sub.status = 'active'
            elif status == 'canceled' or status == 'incomplete_expired':
                sub.status = 'cancelled'
            elif status == 'past_due' or status == 'unpaid':
                sub.status = 'pending'
            
            # Update price if plan changed
            items = getattr(subscription, 'items', None)
            if items and hasattr(items, 'data') and len(items.data) > 0:
                price_id = items.data[0].price.id
                sub.stripe_price_id = price_id
            
            sub.save()
        except BusinessSubscription.DoesNotExist:
            pass

    return HttpResponse(status=200)

@login_required
def bkash_initiate(request, plan_type):
    business_id = request.GET.get('business_id')
    if business_id:
        from django.shortcuts import get_object_or_404
        business = get_object_or_404(BusinessInstance, id=business_id, owner=request.user)
    else:
        business = BusinessInstance.objects.filter(owner=request.user).first()

    if not business:
        return HttpResponse("No business instance found.", status=404)
        
    billing_cycle = request.GET.get('cycle', 'monthly')
    plan = HubPlanConfig.objects.filter(plan_type=plan_type).first()
    if not plan:
        return HttpResponse("Plan not found.", status=404)

    # Convert USD to BDT (mock exchange rate: 110 BDT = 1 USD)
    usd_amount = plan.monthly_price_usd if billing_cycle == 'monthly' else plan.annual_price_usd
    bdt_amount = usd_amount * 110
    
    invoice_id = str(uuid.uuid4())[:8] + f"-{business.id}"
    
    # Save the pending subscription intent to session
    request.session['bkash_pending_plan'] = plan_type
    request.session['bkash_pending_cycle'] = billing_cycle
    request.session['bkash_pending_biz'] = business.id

    base_url = request.build_absolute_uri('/')[:-1]
    callback_url = f"{base_url}/billing/bkash/callback/"

    bkash = BKashService()
    payment_res = bkash.create_payment(amount=bdt_amount, invoice_id=invoice_id, callback_url=callback_url)
    
    if payment_res and 'bkashURL' in payment_res:
        return redirect(payment_res['bkashURL'])
    else:
        # Mock successful redirect if credentials fail (sandbox mode bypass)
        if not getattr(settings, 'BKASH_APP_KEY', ''):
            request.session['bkash_mock_payment_id'] = f"TRX-{uuid.uuid4()}"
            return redirect(f"{callback_url}?paymentID={request.session['bkash_mock_payment_id']}&status=success")
            
        return HttpResponse(f"bKash error: {payment_res.get('statusMessage', 'Unknown')}", status=400)

@login_required
def bkash_callback(request):
    payment_id = request.GET.get('paymentID')
    status = request.GET.get('status')
    
    business_id = request.session.get('bkash_pending_biz')
    plan_type = request.session.get('bkash_pending_plan')
    billing_cycle = request.session.get('bkash_pending_cycle')
    
    if not business_id:
        return redirect('console_admin:dashboard')

    if status == 'success' or status == 'completed':
        # Bypass for sandbox testing without real credentials
        if request.session.get('bkash_mock_payment_id') == payment_id:
            execute_res = {"statusCode": "0000", "transactionStatus": "Completed"}
        else:
            bkash = BKashService()
            execute_res = bkash.execute_payment(payment_id)
            
        if execute_res.get('statusCode') == '0000' or execute_res.get('transactionStatus') == 'Completed':
            business = BusinessInstance.objects.get(id=business_id)
            sub, created = BusinessSubscription.objects.get_or_create(business=business)
            sub.status = 'active'
            sub.plan_type = plan_type
            sub.billing_cycle = billing_cycle
            sub.stripe_subscription_id = f"bkash_{payment_id}" # store bkash ref here for simplicity
            sub.save()

            try:
                from bengalbound_core.notifications import send_slack_alert
                send_slack_alert(
                    title="💰 New Subscription (bKash) 💰",
                    message=f"Business: {business.name} ({business.slug})\nPlan: {plan_type} ({billing_cycle})",
                    urgency="high"
                )
            except Exception as e:
                pass
            
            return redirect(f'/billing/success/?business_id={business.id}')
            
    return redirect(f'/billing/cancel/?business_id={business_id}')

@login_required
def bkash_cancel(request):
    business_id = request.session.get('bkash_pending_biz')
    if business_id:
        return redirect(f'/billing/cancel/?business_id={business_id}')
    return redirect('console_admin:dashboard')
