import stripe
from django.conf import settings
from .models import StripeCustomer
from hub.models import HubPlanConfig

stripe.api_key = settings.STRIPE_SECRET_KEY

def get_or_create_stripe_customer(business):
    """
    Retrieve existing StripeCustomer or create a new one in Stripe and map it.
    """
    try:
        stripe_cust = business.stripe_customer
        return stripe_cust.stripe_customer_id
    except StripeCustomer.DoesNotExist:
        # Create customer in Stripe
        customer = stripe.Customer.create(
            email=business.owner.email,
            name=business.name,
            metadata={
                'business_id': business.id,
                'business_slug': business.slug
            }
        )
        StripeCustomer.objects.create(business=business, stripe_customer_id=customer.id)
        return customer.id

def create_checkout_session(business, plan_type, billing_cycle, base_url):
    """
    Create a Stripe Checkout session for a specific plan.
    """
    customer_id = get_or_create_stripe_customer(business)
    
    plan = HubPlanConfig.objects.filter(plan_type=plan_type).first()
    if not plan:
        raise ValueError("Plan not found")

    amount = plan.monthly_price_usd if billing_cycle == 'monthly' else plan.annual_price_usd
    interval = 'month' if billing_cycle == 'monthly' else 'year'
    
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f"BengalBound {plan.get_plan_type_display()} Plan",
                },
                'unit_amount': int(amount * 100),
                'recurring': {
                    'interval': interval,
                },
            },
            'quantity': 1,
        }],
        mode='subscription',
        success_url=f"{base_url}/billing/success/?session_id={{CHECKOUT_SESSION_ID}}&business_id={business.id}",
        cancel_url=f"{base_url}/billing/cancel/?business_id={business.id}",
        client_reference_id=str(business.id),
        metadata={
            'plan_type': plan_type,
            'billing_cycle': billing_cycle
        }
    )
    return session.url

def create_portal_session(business, base_url):
    """
    Create a Stripe Customer Portal session.
    """
    customer_id = get_or_create_stripe_customer(business)
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{base_url}/console/"
    )
    return session.url

def create_ai_checkout_session(user, tier, duration_months, base_url, agent_slug=None):
    """
    Create a Stripe Checkout session for hiring an AI Employee.
    """
    try:
        from .models import StripeCustomer
        # For individual users hiring AI agents without a business context
        # (Though they usually have a business, we link it to the user here)
        customer_list = stripe.Customer.list(email=user.email, limit=1)
        if customer_list.data:
            customer_id = customer_list.data[0].id
        else:
            customer = stripe.Customer.create(email=user.email, name=user.email)
            customer_id = customer.id
    except Exception:
        customer_id = None

    amount = float(tier.monthly_price_usd)
    
    # We will use one-time payment for the duration months instead of subscription
    # to avoid complex stripe subscription proration unless requested.
    # We set mode='payment'
    
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f"{tier.get_name_display()} AI Employee",
                    'description': f"{duration_months} Month(s) Hire",
                },
                'unit_amount': int(amount * 100),
            },
            'quantity': duration_months,
        }],
        mode='payment',
        success_url=f"{base_url}/console/dashboard/",
        cancel_url=f"{base_url}/console/hire-ai/",
        client_reference_id=str(user.id),
        metadata={
            'type': 'ai_employee',
            'tier_id': str(tier.id),
            'duration_months': str(duration_months),
            'agent_slug': agent_slug or ''
        }
    )
    return session.url
