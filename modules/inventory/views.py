from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q

from hub.views import _get_business_for_user
from .models import Product, ProductCategory, Warehouse, StockLevel, StockMovement, UnitOfMeasure


def _biz(slug, user):
    return _get_business_for_user(slug, user)


def _ensure_warehouse(biz):
    wh, _ = Warehouse.objects.get_or_create(business=biz, name='Main Warehouse', defaults={'code': 'WH01', 'is_active': True})
    return wh


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    wh = _ensure_warehouse(biz)
    stats = {
        'total_products': Product.objects.filter(business=biz, is_active=True).count(),
        'categories': ProductCategory.objects.filter(business=biz).count(),
        'warehouses': Warehouse.objects.filter(business=biz, is_active=True).count(),
        'low_stock': StockLevel.objects.filter(warehouse__business=biz, quantity__lte=0).count(),
    }
    recent_movements = StockMovement.objects.filter(business=biz).order_by('-movement_date')[:10]
    return render(request, 'inventory/index.html', {'biz': biz, 'stats': stats, 'recent_movements': recent_movements})


@login_required(login_url='/accounts/login/')
def products(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    q = request.GET.get('q', '')
    category = request.GET.get('cat', '')
    qs = Product.objects.filter(business=biz).select_related('category')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(barcode__icontains=q))
    if category:
        qs = qs.filter(category_id=category)
    categories = ProductCategory.objects.filter(business=biz)
    return render(request, 'inventory/products.html', {'biz': biz, 'products': qs, 'categories': categories, 'q': q, 'cat': category})


@login_required(login_url='/accounts/login/')
def product_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    categories = ProductCategory.objects.filter(business=biz)
    uoms = UnitOfMeasure.objects.filter(business=biz)
    if request.method == 'POST':
        p = Product.objects.create(
            business=biz,
            name=request.POST.get('name', '').strip(),
            sku=request.POST.get('sku', '').strip(),
            barcode=request.POST.get('barcode', '').strip(),
            product_type=request.POST.get('product_type', 'storable'),
            category_id=request.POST.get('category') or None,
            cost_price=request.POST.get('cost_price') or 0,
            sale_price=request.POST.get('sale_price') or 0,
            reorder_level=request.POST.get('reorder_level') or 0,
            description=request.POST.get('description', '').strip(),
        )
        messages.success(request, f'Product "{p.name}" created.')
        return redirect('inventory:products', slug=slug)
    return render(request, 'inventory/product_form.html', {'biz': biz, 'categories': categories, 'uoms': uoms})


@login_required(login_url='/accounts/login/')
def product_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    product = get_object_or_404(Product, pk=pk, business=biz)
    stock_levels = product.stock_levels.select_related('warehouse')
    movements = product.movements.order_by('-movement_date')[:20]
    warehouses = Warehouse.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            product.name = request.POST.get('name', product.name).strip() or product.name
            product.sale_price = request.POST.get('sale_price', product.sale_price)
            product.cost_price = request.POST.get('cost_price', product.cost_price)
            product.reorder_level = request.POST.get('reorder_level', product.reorder_level)
            product.description = request.POST.get('description', product.description)
            product.save()
            messages.success(request, 'Product updated.')
        elif action == 'delete':
            product.delete()
            messages.success(request, 'Product deleted.')
            return redirect('inventory:products', slug=slug)
        elif action == 'adjust_stock':
            wh = get_object_or_404(Warehouse, pk=request.POST.get('warehouse'), business=biz)
            qty = float(request.POST.get('qty', 0))
            mv = StockMovement.objects.create(
                business=biz, product=product, movement_type='adjustment',
                to_warehouse=wh, quantity=qty, notes=request.POST.get('notes', ''),
                created_by=request.user,
            )
            mv.confirm()
            messages.success(request, f'Stock adjusted by {qty}.')
        return redirect('inventory:product_detail', slug=slug, pk=pk)
    return render(request, 'inventory/product_detail.html', {'biz': biz, 'product': product, 'stock_levels': stock_levels, 'movements': movements, 'warehouses': warehouses})


@login_required(login_url='/accounts/login/')
def warehouses(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Warehouse.objects.create(business=biz, name=request.POST.get('name', '').strip(), code=request.POST.get('code', '').strip(), address=request.POST.get('address', ''))
            messages.success(request, 'Warehouse created.')
        elif action == 'delete':
            Warehouse.objects.filter(pk=request.POST.get('wh_id'), business=biz).delete()
            messages.success(request, 'Warehouse deleted.')
        return redirect('inventory:warehouses', slug=slug)
    whs = Warehouse.objects.filter(business=biz)
    return render(request, 'inventory/warehouses.html', {'biz': biz, 'warehouses': whs})


@login_required(login_url='/accounts/login/')
def movements(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    qs = StockMovement.objects.filter(business=biz).select_related('product', 'from_warehouse', 'to_warehouse').order_by('-movement_date')
    return render(request, 'inventory/movements.html', {'biz': biz, 'movements': qs})
