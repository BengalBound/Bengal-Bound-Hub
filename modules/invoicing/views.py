from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import Invoice, InvoiceLine, InvoiceClient, Payment


def _biz(slug, user):
    return _get_business_for_user(slug, user)


def _next_invoice_number(biz):
    count = Invoice.objects.filter(business=biz).count() + 1
    return f"{count:04d}"


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    invoices = Invoice.objects.filter(business=biz)
    stats = {
        'total': invoices.count(),
        'draft': invoices.filter(status='draft').count(),
        'sent': invoices.filter(status__in=['sent', 'viewed']).count(),
        'overdue': sum(1 for i in invoices if i.is_overdue),
        'total_outstanding': invoices.exclude(status__in=['paid', 'cancelled']).aggregate(s=Sum('total'))['s'] or 0,
        'total_paid': invoices.filter(status='paid').aggregate(s=Sum('total'))['s'] or 0,
    }
    recent = invoices.order_by('-issue_date')[:10]
    return render(request, 'invoicing/index.html', {'biz': biz, 'stats': stats, 'recent_invoices': recent})


@login_required(login_url='/accounts/login/')
def invoice_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status = request.GET.get('status', '')
    q = request.GET.get('q', '')
    qs = Invoice.objects.filter(business=biz).select_related('client').order_by('-issue_date')
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(invoice_number__icontains=q) | Q(client__name__icontains=q))
    return render(request, 'invoicing/invoice_list.html', {'biz': biz, 'invoices': qs, 'status_filter': status, 'q': q})


@login_required(login_url='/accounts/login/')
def invoice_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    clients = InvoiceClient.objects.filter(business=biz)
    if request.method == 'POST':
        client_id = request.POST.get('client') or None
        if not client_id:
            client = InvoiceClient.objects.create(
                business=biz, name=request.POST.get('client_name', '').strip(),
                email=request.POST.get('client_email', '').strip(),
            )
            client_id = client.pk
        inv = Invoice.objects.create(
            business=biz, invoice_number=_next_invoice_number(biz),
            client_id=client_id,
            issue_date=request.POST.get('issue_date', timezone.now().date()),
            due_date=request.POST.get('due_date') or None,
            notes=request.POST.get('notes', ''), terms=request.POST.get('terms', ''),
            created_by=request.user,
        )
        descs = request.POST.getlist('item_desc')
        qtys = request.POST.getlist('item_qty')
        prices = request.POST.getlist('item_price')
        for i, desc in enumerate(descs):
            if desc.strip():
                InvoiceLine.objects.create(
                    invoice=inv, description=desc.strip(),
                    quantity=qtys[i] if i < len(qtys) else 1,
                    unit_price=prices[i] if i < len(prices) else 0,
                )
        inv.recalculate()
        messages.success(request, f'Invoice #{inv.invoice_number} created.')
        return redirect('invoicing:invoice_detail', slug=slug, pk=inv.pk)
    return render(request, 'invoicing/invoice_form.html', {'biz': biz, 'clients': clients})


@login_required(login_url='/accounts/login/')
def invoice_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    inv = get_object_or_404(Invoice, pk=pk, business=biz)
    payments = inv.payments.order_by('-payment_date')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send':
            inv.status = 'sent'
            inv.save(update_fields=['status'])
            messages.success(request, 'Invoice marked as sent.')
        elif action == 'record_payment':
            amount = float(request.POST.get('amount', 0))
            Payment.objects.create(
                invoice=inv, amount=amount,
                payment_date=request.POST.get('payment_date', timezone.now().date()),
                method=request.POST.get('method', 'bank_transfer'),
                reference=request.POST.get('reference', ''),
                recorded_by=request.user,
            )
            inv.amount_paid = (inv.amount_paid or 0) + amount
            if inv.amount_paid >= inv.total:
                inv.status = 'paid'
            elif inv.amount_paid > 0:
                inv.status = 'partial'
            inv.save(update_fields=['amount_paid', 'status'])
            messages.success(request, f'Payment of {amount} recorded.')
        elif action == 'cancel':
            inv.status = 'cancelled'
            inv.save(update_fields=['status'])
            messages.info(request, 'Invoice cancelled.')
        elif action == 'delete':
            inv.delete()
            messages.success(request, 'Invoice deleted.')
            return redirect('invoicing:invoice_list', slug=slug)
        return redirect('invoicing:invoice_detail', slug=slug, pk=pk)
    return render(request, 'invoicing/invoice_detail.html', {'biz': biz, 'invoice': inv, 'payments': payments})


@login_required(login_url='/accounts/login/')
def clients(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            InvoiceClient.objects.create(
                business=biz, name=request.POST.get('name', '').strip(),
                email=request.POST.get('email', '').strip(), phone=request.POST.get('phone', ''),
                company=request.POST.get('company', ''), address=request.POST.get('address', ''),
            )
            messages.success(request, 'Client added.')
        elif action == 'delete':
            InvoiceClient.objects.filter(pk=request.POST.get('client_id'), business=biz).delete()
            messages.success(request, 'Client removed.')
        return redirect('invoicing:clients', slug=slug)
    all_clients = InvoiceClient.objects.filter(business=biz)
    return render(request, 'invoicing/clients.html', {'biz': biz, 'clients': all_clients})
