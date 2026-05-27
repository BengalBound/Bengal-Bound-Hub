"""
console_admin/views_billing.py
Billing portal — invoice history, payment receipts, plan change UI.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv

from .decorators import console_user_required
from workspace_admin.models import Subscription, Order, HiredAIEmployee, AIEmployeeTier


@console_user_required(login_url='/accounts/login/')
def billing_overview(request):
    """Invoice & subscription history dashboard."""
    subscriptions = Subscription.objects.filter(
        client=request.user
    ).select_related('tier', 'hired_ai').order_by('-started_at')

    orders = Order.objects.filter(client=request.user).order_by('-created_at')

    sub_paginator = Paginator(subscriptions, 10)
    ord_paginator = Paginator(orders, 15)

    sub_page = sub_paginator.get_page(request.GET.get('sub_page'))
    ord_page = ord_paginator.get_page(request.GET.get('ord_page'))

    # Active plan summary
    active_sub = subscriptions.filter(status='active').first()

    return render(request, 'console_admin/billing_overview.html', {
        'subscriptions': sub_page,
        'orders': ord_page,
        'active_sub': active_sub,
    })


@console_user_required(login_url='/accounts/login/')
def billing_invoice_detail(request, sub_id):
    """Single subscription / invoice receipt view."""
    sub = get_object_or_404(Subscription, id=sub_id, client=request.user)
    return render(request, 'console_admin/billing_invoice_detail.html', {'sub': sub})


@console_user_required(login_url='/accounts/login/')
def billing_invoice_pdf(request, sub_id):
    """Download invoice as CSV receipt (lightweight PDF alternative)."""
    sub = get_object_or_404(Subscription, id=sub_id, client=request.user)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="invoice-{sub.id}.csv"'
    writer = csv.writer(response)
    writer.writerow(['BengalBound Invoice Receipt'])
    writer.writerow([])
    writer.writerow(['Invoice #', sub.id])
    writer.writerow(['Client', request.user.email])
    writer.writerow(['Plan / Tier', str(sub.tier)])
    writer.writerow(['Billing Cycle', sub.get_billing_cycle_display()])
    writer.writerow(['Status', sub.get_status_display()])
    writer.writerow(['Amount Paid', f'${sub.amount_paid_usd}'])
    writer.writerow(['Started', sub.started_at.strftime('%Y-%m-%d') if sub.started_at else ''])
    writer.writerow(['Period End', sub.current_period_end.strftime('%Y-%m-%d') if sub.current_period_end else ''])
    writer.writerow(['NowPayments Order ID', sub.nowpayments_order_id or '—'])
    return response


@console_user_required(login_url='/accounts/login/')
def billing_plan_change(request):
    """Let the client upgrade or change their AI tier subscription."""
    tiers = AIEmployeeTier.objects.all().order_by('monthly_price_usd')
    hired_ai = HiredAIEmployee.objects.filter(employer=request.user, is_active=True).first()
    current_tier = hired_ai.tier if hired_ai else None

    if request.method == 'POST':
        tier_id = request.POST.get('tier_id')
        tier = get_object_or_404(AIEmployeeTier, id=tier_id)

        if current_tier and tier == current_tier:
            messages.info(request, "You are already on this plan.")
            return redirect('console_admin:billing_plan_change')

        if tier.monthly_price_usd > 0:
            # Redirect to NowPayments checkout — reuse hire_ai payment logic
            return redirect(f'/hire-ai/?tier={tier_id}&upgrade=1')

        # Free tier — apply immediately
        if hired_ai:
            hired_ai.tier = tier
            hired_ai.save(update_fields=['tier'])
            messages.success(request, f"Plan changed to {tier.get_name_display()}.")
        return redirect('console_admin:billing_overview')

    return render(request, 'console_admin/billing_plan_change.html', {
        'tiers': tiers,
        'current_tier': current_tier,
    })
