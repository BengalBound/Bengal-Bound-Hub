from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone

from hub.views import _get_business_for_user
from hub.access import get_access_level
from .models import (
    ERPLedger, ERPJournalEntry, ERPJournalLine,
    ERPVendor, ERPPurchaseOrder, ERPPurchaseOrderLine,
    ERPCostCenter, ERPBudgetLine,
)


def _erp_check(slug, user, min_level=4):
    biz = _get_business_for_user(slug, user)
    if not biz:
        return None, HttpResponseForbidden()
    if get_access_level(biz, user) < min_level:
        return None, HttpResponseForbidden()
    return biz, None


@login_required(login_url='/accounts/login/')
def erp_dashboard(request, slug):
    biz, err = _erp_check(slug, request.user)
    if err:
        return err

    ledger_count = ERPLedger.objects.filter(business=biz, is_active=True).count()
    vendor_count = ERPVendor.objects.filter(business=biz, is_active=True).count()
    open_pos = ERPPurchaseOrder.objects.filter(business=biz, status__in=['draft', 'sent', 'partial']).count()
    recent_entries = ERPJournalEntry.objects.filter(business=biz).order_by('-entry_date')[:5]

    return render(request, 'erp/dashboard.html', {
        'biz': biz,
        'ledger_count': ledger_count,
        'vendor_count': vendor_count,
        'open_pos': open_pos,
        'recent_entries': recent_entries,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def erp_ledger(request, slug):
    biz, err = _erp_check(slug, request.user)
    if err:
        return err

    if request.method == 'POST':
        if get_access_level(biz, request.user) < 7:
            return HttpResponseForbidden()
        ERPLedger.objects.create(
            business=biz,
            account_code=request.POST.get('account_code', '').strip(),
            account_name=request.POST.get('account_name', '').strip(),
            account_type=request.POST.get('account_type', 'expense'),
        )
        messages.success(request, "Account created.")
        return redirect('erp:ledger', slug=slug)

    accounts = ERPLedger.objects.filter(business=biz).order_by('account_code')
    return render(request, 'erp/ledger.html', {
        'biz': biz,
        'accounts': accounts,
        'account_types': ERPLedger.ACCOUNT_TYPES,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def erp_journal(request, slug):
    biz, err = _erp_check(slug, request.user)
    if err:
        return err

    entries = ERPJournalEntry.objects.filter(business=biz).order_by('-entry_date')[:50]
    return render(request, 'erp/journal.html', {
        'biz': biz,
        'entries': entries,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def erp_journal_create(request, slug):
    biz, err = _erp_check(slug, request.user, min_level=5)
    if err:
        return err

    if request.method == 'POST':
        entry = ERPJournalEntry.objects.create(
            business=biz,
            reference=request.POST.get('reference', '').strip(),
            description=request.POST.get('description', '').strip(),
            entry_date=request.POST.get('entry_date') or timezone.localdate(),
            created_by=request.user,
        )
        messages.success(request, f"Journal entry JE-{entry.pk} created as draft.")
        return redirect('erp:journal', slug=slug)

    accounts = ERPLedger.objects.filter(business=biz, is_active=True)
    return render(request, 'erp/journal_form.html', {
        'biz': biz,
        'accounts': accounts,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def erp_vendors(request, slug):
    biz, err = _erp_check(slug, request.user)
    if err:
        return err

    if request.method == 'POST':
        ERPVendor.objects.create(
            business=biz,
            name=request.POST.get('name', '').strip(),
            contact_name=request.POST.get('contact_name', '').strip(),
            email=request.POST.get('email', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            address=request.POST.get('address', '').strip(),
            tax_id=request.POST.get('tax_id', '').strip(),
            payment_terms_days=int(request.POST.get('payment_terms_days', 30)),
        )
        messages.success(request, "Vendor added.")
        return redirect('erp:vendors', slug=slug)

    vendors = ERPVendor.objects.filter(business=biz, is_active=True).order_by('name')
    return render(request, 'erp/vendors.html', {
        'biz': biz,
        'vendors': vendors,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def erp_purchase_orders(request, slug):
    biz, err = _erp_check(slug, request.user)
    if err:
        return err

    pos = ERPPurchaseOrder.objects.filter(business=biz).select_related('vendor')
    status_filter = request.GET.get('status', '')
    if status_filter:
        pos = pos.filter(status=status_filter)

    return render(request, 'erp/purchase_orders.html', {
        'biz': biz,
        'pos': pos,
        'status_filter': status_filter,
        'statuses': ERPPurchaseOrder.STATUS,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def erp_purchase_order_detail(request, slug, po_id):
    biz, err = _erp_check(slug, request.user)
    if err:
        return err

    po = get_object_or_404(ERPPurchaseOrder, pk=po_id, business=biz)
    return render(request, 'erp/po_detail.html', {
        'biz': biz,
        'po': po,
        'lines': po.lines.all(),
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def erp_cost_centers(request, slug):
    biz, err = _erp_check(slug, request.user, min_level=6)
    if err:
        return err

    if request.method == 'POST':
        from hub.models import BusinessEmployee
        manager_id = request.POST.get('manager_id', '')
        ERPCostCenter.objects.create(
            business=biz,
            code=request.POST.get('code', '').strip(),
            name=request.POST.get('name', '').strip(),
            manager_id=int(manager_id) if manager_id else None,
        )
        messages.success(request, "Cost center created.")
        return redirect('erp:cost_centers', slug=slug)

    from hub.models import BusinessEmployee
    centers = ERPCostCenter.objects.filter(business=biz, is_active=True)
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    return render(request, 'erp/cost_centers.html', {
        'biz': biz,
        'centers': centers,
        'employees': employees,
        'is_owner': biz.owner == request.user,
    })
