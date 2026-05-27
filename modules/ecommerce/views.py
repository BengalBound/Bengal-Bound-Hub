from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils.text import slugify

from hub.views import _get_business_for_user
from .models import Store, StoreCategory, StoreProduct, Order, OrderItem


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    stores = Store.objects.filter(business=biz)
    stats = {
        'stores': stores.count(),
        'products': StoreProduct.objects.filter(store__business=biz, status='active').count(),
        'orders': Order.objects.filter(store__business=biz).count(),
        'pending_orders': Order.objects.filter(store__business=biz, status='pending').count(),
    }
    recent_orders = Order.objects.filter(store__business=biz).order_by('-created_at')[:10]
    return render(request, 'ecommerce/index.html', {
        'biz': biz, 'stores': stores, 'stats': stats, 'recent_orders': recent_orders,
    })


@login_required(login_url='/accounts/login/')
def store_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            name = request.POST.get('name', '').strip()
            store_slug = slugify(name)
            base = store_slug
            i = 1
            while Store.objects.filter(slug=store_slug).exists():
                store_slug = f"{base}-{i}"
                i += 1
            Store.objects.create(
                business=biz, name=name, slug=store_slug,
                description=request.POST.get('description', ''),
                currency=request.POST.get('currency', 'USD'),
                tax_rate=request.POST.get('tax_rate', 0) or 0,
            )
            messages.success(request, f'Store "{name}" created.')
        elif action == 'delete':
            Store.objects.filter(pk=request.POST.get('store_id'), business=biz).delete()
            messages.success(request, 'Store deleted.')
        return redirect('ecommerce:store_list', slug=slug)
    stores = Store.objects.filter(business=biz)
    return render(request, 'ecommerce/store_list.html', {'biz': biz, 'stores': stores})


@login_required(login_url='/accounts/login/')
def products(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    stores = Store.objects.filter(business=biz)
    store_id = request.GET.get('store', '')
    qs = StoreProduct.objects.filter(store__business=biz).select_related('store', 'category')
    if store_id:
        qs = qs.filter(store_id=store_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            store = get_object_or_404(Store, pk=request.POST.get('store'), business=biz)
            name = request.POST.get('name', '').strip()
            prod_slug = slugify(name)
            StoreProduct.objects.create(
                store=store, name=name, slug=prod_slug,
                description=request.POST.get('description', ''),
                product_type=request.POST.get('product_type', 'physical'),
                sku=request.POST.get('sku', '').strip(),
                price=request.POST.get('price', 0) or 0,
                stock=request.POST.get('stock', 0) or 0,
                status=request.POST.get('status', 'draft'),
                created_by=request.user,
            )
            messages.success(request, f'Product "{name}" created.')
        elif action == 'delete':
            StoreProduct.objects.filter(pk=request.POST.get('product_id'), store__business=biz).delete()
            messages.success(request, 'Product deleted.')
        return redirect('ecommerce:products', slug=slug)
    return render(request, 'ecommerce/products.html', {
        'biz': biz, 'products': qs, 'stores': stores, 'store_filter': store_id,
    })


@login_required(login_url='/accounts/login/')
def orders(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status_filter = request.GET.get('status', '')
    qs = Order.objects.filter(store__business=biz).order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'ecommerce/orders.html', {
        'biz': biz, 'orders': qs, 'status_filter': status_filter,
    })


@login_required(login_url='/accounts/login/')
def order_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    order = get_object_or_404(Order, pk=pk, store__business=biz)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            order.status = request.POST.get('status', order.status)
            order.tracking_number = request.POST.get('tracking_number', order.tracking_number)
            order.save(update_fields=['status', 'tracking_number'])
            messages.success(request, 'Order updated.')
        elif action == 'delete':
            order.delete()
            messages.success(request, 'Order deleted.')
            return redirect('ecommerce:orders', slug=slug)
        return redirect('ecommerce:order_detail', slug=slug, pk=pk)
    return render(request, 'ecommerce/order_detail.html', {
        'biz': biz, 'order': order, 'items': order.items.all(),
    })
