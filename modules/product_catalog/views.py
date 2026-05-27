from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hub.models import BusinessInstance, BusinessEmployee
from .models import ProductCatalog, CatalogCategory, CatalogItem


def _pc_check(slug, user, min_level=1):
    biz = get_object_or_404(BusinessInstance, slug=slug)
    try:
        emp = BusinessEmployee.objects.get(business=biz, user=user, is_active=True)
    except BusinessEmployee.DoesNotExist:
        return None, None, None
    level = emp.access_level_numeric
    if level < min_level:
        return biz, emp, None
    return biz, emp, level


@login_required
def catalog_home(request, slug):
    biz, emp, level = _pc_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    catalogs = ProductCatalog.objects.filter(business=biz)
    stats = {
        'catalogs': catalogs.count(),
        'public': catalogs.filter(is_public=True).count(),
        'items': CatalogItem.objects.filter(catalog__business=biz).count(),
        'featured': CatalogItem.objects.filter(catalog__business=biz, is_featured=True).count(),
    }

    return render(request, 'product_catalog/home.html', {
        'biz': biz, 'access_level': level, 'catalogs': catalogs, 'stats': stats,
    })


@login_required
def catalog_detail(request, slug, catalog_id):
    biz, emp, level = _pc_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    catalog = get_object_or_404(ProductCatalog, pk=catalog_id, business=biz)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_category':
            CatalogCategory.objects.create(
                catalog=catalog,
                name=request.POST['category_name'],
                display_order=request.POST.get('display_order', 0),
            )
            messages.success(request, 'Category added.')
        elif action == 'add_item':
            cat_id = request.POST.get('category_id')
            category = CatalogCategory.objects.filter(pk=cat_id, catalog=catalog).first() if cat_id else None
            CatalogItem.objects.create(
                catalog=catalog,
                category=category,
                name=request.POST['name'],
                sku=request.POST.get('sku', ''),
                description=request.POST.get('description', ''),
                price=request.POST.get('price') or None,
                currency=request.POST.get('currency', 'USD'),
                unit=request.POST.get('unit', ''),
                is_featured='is_featured' in request.POST,
                in_stock='in_stock' in request.POST,
            )
            messages.success(request, 'Item added.')
        elif action == 'delete_item':
            CatalogItem.objects.filter(pk=request.POST.get('item_id'), catalog=catalog).delete()
        elif action == 'share':
            catalog.generate_share_token()
            messages.success(request, 'Share link generated.')
        elif action == 'unshare':
            catalog.is_public = False
            catalog.share_token = ''
            catalog.save(update_fields=['is_public', 'share_token'])
            messages.success(request, 'Catalog is now private.')
        return redirect('product_catalog:catalog_detail', slug=slug, catalog_id=catalog_id)

    categories = catalog.categories.all()
    items = catalog.items.select_related('category').all()
    share_url = None
    if catalog.is_public and catalog.share_token:
        share_url = request.build_absolute_uri(f"/catalog/{catalog.share_token}/")

    return render(request, 'product_catalog/catalog_detail.html', {
        'biz': biz, 'access_level': level, 'catalog': catalog,
        'categories': categories, 'items': items, 'share_url': share_url,
    })


@login_required
def catalog_create(request, slug):
    biz, emp, level = _pc_check(slug, request.user, min_level=3)
    if not level:
        return redirect('product_catalog:catalog_home', slug=slug)

    if request.method == 'POST':
        cat = ProductCatalog.objects.create(
            business=biz,
            title=request.POST['title'],
            description=request.POST.get('description', ''),
            created_by=emp,
        )
        messages.success(request, f'Catalog "{cat.title}" created.')
        return redirect('product_catalog:catalog_detail', slug=slug, catalog_id=cat.pk)

    return render(request, 'product_catalog/catalog_form.html', {'biz': biz, 'access_level': level})


def catalog_public(request, token):
    catalog = get_object_or_404(ProductCatalog, share_token=token, is_public=True)
    categories = catalog.categories.prefetch_related('items').all()
    uncategorized = catalog.items.filter(category__isnull=True)
    return render(request, 'product_catalog/catalog_public.html', {
        'catalog': catalog, 'categories': categories, 'uncategorized': uncategorized,
    })
