from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import PurchaseOrder, PurchaseOrderLine, Vendor


def _biz(slug, user):
    return _get_business_for_user(slug, user)


def _next_po_number(biz):
    count = PurchaseOrder.objects.filter(business=biz).count() + 1
    return f"PO-{count:04d}"


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    orders = PurchaseOrder.objects.filter(business=biz)
    stats = {
        'total': orders.count(),
        'pending': orders.filter(status='draft').count(),
        'in_transit': orders.filter(status='confirmed').count(),
        'total_value': orders.aggregate(s=Sum('total'))['s'] or 0,
    }
    recent = orders.order_by('-order_date')[:10]
    return render(request, 'order_mgmt/index.html', {'biz': biz, 'stats': stats, 'recent_orders': recent})


@login_required(login_url='/accounts/login/')
def purchase_orders(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status = request.GET.get('status', '')
    q = request.GET.get('q', '')
    qs = PurchaseOrder.objects.filter(business=biz).select_related('vendor').order_by('-order_date')
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(po_number__icontains=q) | Q(vendor__name__icontains=q))
    return render(request, 'order_mgmt/purchase_orders.html', {'biz': biz, 'orders': qs, 'status_filter': status, 'q': q})


@login_required(login_url='/accounts/login/')
def po_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    vendors = Vendor.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        vendor = get_object_or_404(Vendor, pk=request.POST.get('vendor'), business=biz)
        po = PurchaseOrder.objects.create(
            business=biz, po_number=_next_po_number(biz), vendor=vendor,
            order_date=request.POST.get('order_date', timezone.now().date()),
            expected_date=request.POST.get('expected_date') or None,
            notes=request.POST.get('notes', ''), created_by=request.user,
        )
        descs = request.POST.getlist('item_desc')
        qtys = request.POST.getlist('item_qty')
        prices = request.POST.getlist('item_price')
        for i, desc in enumerate(descs):
            if desc.strip():
                PurchaseOrderLine.objects.create(po=po, description=desc.strip(), quantity=qtys[i] if i < len(qtys) else 1, unit_price=prices[i] if i < len(prices) else 0)
        po.recalculate()
        messages.success(request, f'Purchase order {po.po_number} created.')
        return redirect('order_mgmt:po_detail', slug=slug, pk=po.pk)
    return render(request, 'order_mgmt/po_form.html', {'biz': biz, 'vendors': vendors})


@login_required(login_url='/accounts/login/')
def po_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    po = get_object_or_404(PurchaseOrder, pk=pk, business=biz)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            po.status = request.POST.get('status', po.status)
            po.save(update_fields=['status'])
            messages.success(request, f'PO status updated to {po.status}.')
        elif action == 'delete':
            po.delete()
            messages.success(request, 'Purchase order deleted.')
            return redirect('order_mgmt:purchase_orders', slug=slug)
        return redirect('order_mgmt:po_detail', slug=slug, pk=pk)
    return render(request, 'order_mgmt/po_detail.html', {'biz': biz, 'po': po})


@login_required(login_url='/accounts/login/')
def vendors(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Vendor.objects.create(
                business=biz, name=request.POST.get('name', '').strip(),
                contact_person=request.POST.get('contact_person', ''), email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''), address=request.POST.get('address', ''),
                payment_terms=int(request.POST.get('payment_terms', 30)),
            )
            messages.success(request, 'Vendor added.')
        elif action == 'delete':
            Vendor.objects.filter(pk=request.POST.get('vendor_id'), business=biz).delete()
            messages.success(request, 'Vendor removed.')
        return redirect('order_mgmt:vendors', slug=slug)
    all_vendors = Vendor.objects.filter(business=biz)
    return render(request, 'order_mgmt/vendors.html', {'biz': biz, 'vendors': all_vendors})
