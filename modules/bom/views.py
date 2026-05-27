from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages

from hub.views import _get_business_for_user
from .models import BillOfMaterials, BOMComponent, WorkCenter, BOMOperation, ShoeArticleBOM, ShoeColorwayEntry, ShoeBOMLine

try:
    from modules.inventory.models import Product
except ImportError:
    Product = None


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    boms = BillOfMaterials.objects.filter(business=biz)
    stats = {
        'total_boms': boms.count(),
        'active': boms.filter(status='active').count(),
        'work_centers': WorkCenter.objects.filter(business=biz, is_active=True).count(),
        'products_with_bom': boms.values('product').distinct().count(),
    }
    recent = boms.order_by('-created_at')[:10]
    return render(request, 'bom/index.html', {
        'biz': biz, 'stats': stats, 'recent_boms': recent,
    })


@login_required(login_url='/accounts/login/')
def bom_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status_filter = request.GET.get('status', '')
    qs = BillOfMaterials.objects.filter(business=biz).select_related('product', 'created_by').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    products = Product.objects.filter(business=biz) if Product else []
    return render(request, 'bom/bom_list.html', {
        'biz': biz, 'boms': qs, 'products': products, 'status_filter': status_filter,
    })


@login_required(login_url='/accounts/login/')
def bom_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    products = Product.objects.filter(business=biz) if Product else []
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=request.POST.get('product'), business=biz) if Product else None
        bom = BillOfMaterials.objects.create(
            business=biz,
            product=product,
            bom_type=request.POST.get('bom_type', 'manufacture'),
            version=request.POST.get('version', '1.0').strip(),
            quantity=request.POST.get('quantity', 1) or 1,
            uom=request.POST.get('uom', '').strip(),
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, f'BOM created for {product}.')
        return redirect('bom:bom_detail', slug=slug, pk=bom.pk)
    return render(request, 'bom/bom_form.html', {'biz': biz, 'products': products})


@login_required(login_url='/accounts/login/')
def bom_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    bom = get_object_or_404(BillOfMaterials, pk=pk, business=biz)
    components = bom.components.select_related('product')
    operations = bom.operations.select_related('work_center')
    products = Product.objects.filter(business=biz) if Product else []
    work_centers = WorkCenter.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_component':
            comp_product = get_object_or_404(Product, pk=request.POST.get('component_product'), business=biz) if Product else None
            BOMComponent.objects.create(
                bom=bom,
                product=comp_product,
                quantity=request.POST.get('comp_quantity', 1) or 1,
                uom=request.POST.get('comp_uom', '').strip(),
                scrap_pct=request.POST.get('scrap_pct', 0) or 0,
                position=components.count(),
            )
            messages.success(request, 'Component added.')
        elif action == 'remove_component':
            BOMComponent.objects.filter(pk=request.POST.get('component_id'), bom=bom).delete()
            messages.success(request, 'Component removed.')
        elif action == 'add_operation':
            BOMOperation.objects.create(
                bom=bom,
                name=request.POST.get('op_name', '').strip(),
                work_center_id=request.POST.get('work_center') or None,
                sequence=request.POST.get('sequence', 10) or 10,
                duration_minutes=request.POST.get('duration_minutes', 0) or 0,
                description=request.POST.get('description', ''),
            )
            messages.success(request, 'Operation added.')
        elif action == 'activate':
            bom.status = 'active'
            bom.save(update_fields=['status'])
            messages.success(request, 'BOM activated.')
        elif action == 'delete':
            bom.delete()
            messages.success(request, 'BOM deleted.')
            return redirect('bom:bom_list', slug=slug)
        return redirect('bom:bom_detail', slug=slug, pk=pk)
    return render(request, 'bom/bom_detail.html', {
        'biz': biz, 'bom': bom, 'components': components, 'operations': operations,
        'products': products, 'work_centers': work_centers,
    })


@login_required(login_url='/accounts/login/')
def work_centers(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            WorkCenter.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                code=request.POST.get('code', '').strip(),
                capacity=request.POST.get('capacity', 1) or 1,
                capacity_uom=request.POST.get('capacity_uom', 'units/hour').strip(),
                cost_per_hour=request.POST.get('cost_per_hour', 0) or 0,
            )
            messages.success(request, 'Work center created.')
        elif action == 'delete':
            WorkCenter.objects.filter(pk=request.POST.get('wc_id'), business=biz).delete()
            messages.success(request, 'Work center deleted.')
        return redirect('bom:work_centers', slug=slug)
    all_wcs = WorkCenter.objects.filter(business=biz)
    return render(request, 'bom/work_centers.html', {'biz': biz, 'work_centers': all_wcs})


# ── Shoe Article BOM Views ────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def shoe_bom_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    if request.method == 'POST':
        import datetime
        ShoeArticleBOM.objects.create(
            business=biz,
            article_code=request.POST['article_code'].strip(),
            article_name=request.POST.get('article_name', '').strip(),
            last_code=request.POST.get('last_code', '').strip(),
            size_run=request.POST.get('size_run', '').strip(),
            sample_size=request.POST.get('sample_size', '').strip(),
            buyer=request.POST.get('buyer', '').strip(),
            date=request.POST.get('date') or None,
            notes=request.POST.get('notes', '').strip(),
            created_by=request.user,
        )
        messages.success(request, 'Shoe BOM created.')
        return redirect('bom:shoe_bom_list', slug=slug)

    boms = ShoeArticleBOM.objects.filter(business=biz).prefetch_related('colorways', 'bom_lines')
    return render(request, 'bom/shoe_bom_list.html', {
        'biz': biz, 'boms': boms,
    })


@login_required(login_url='/accounts/login/')
def shoe_bom_detail(request, slug, bom_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    bom = get_object_or_404(ShoeArticleBOM, pk=bom_id, business=biz)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_colorway':
            import json
            # Build size_data from individual size fields submitted as size_XX=qty
            raw_sizes = {}
            for key, val in request.POST.items():
                if key.startswith('size_') and val.strip():
                    size_label = key[5:]
                    try:
                        raw_sizes[size_label] = int(val)
                    except ValueError:
                        pass
            ShoeColorwayEntry.objects.create(
                bom=bom,
                leather_code=request.POST['leather_code'].strip(),
                size_data=raw_sizes,
                pairs_per_carton=request.POST.get('pairs_per_carton', 12) or 12,
                sets=request.POST.get('sets', 1) or 1,
            )
            messages.success(request, 'Colorway added.')

        elif action == 'delete_colorway':
            ShoeColorwayEntry.objects.filter(pk=request.POST.get('colorway_id'), bom=bom).delete()
            messages.success(request, 'Colorway removed.')

        elif action == 'add_line':
            colorway_id = request.POST.get('colorway_id') or None
            line = ShoeBOMLine(
                bom=bom,
                colorway_id=colorway_id if colorway_id else None,
                category=request.POST.get('category', 'upper'),
                material_name=request.POST['material_name'].strip(),
                uom=request.POST.get('uom', 'S/ft').strip(),
                cons_per_pair=request.POST.get('cons_per_pair', 1) or 1,
                order_qty=request.POST.get('order_qty') or None,
                conversion_note=request.POST.get('conversion_note', '').strip(),
                unit_price=request.POST.get('unit_price') or None,
                position=bom.bom_lines.count(),
            )
            line.save()
            messages.success(request, 'Material line added.')

        elif action == 'delete_line':
            ShoeBOMLine.objects.filter(pk=request.POST.get('line_id'), bom=bom).delete()
            messages.success(request, 'Line removed.')

        elif action == 'update_header':
            bom.article_code = request.POST.get('article_code', bom.article_code).strip()
            bom.article_name = request.POST.get('article_name', bom.article_name).strip()
            bom.last_code = request.POST.get('last_code', bom.last_code).strip()
            bom.size_run = request.POST.get('size_run', bom.size_run).strip()
            bom.buyer = request.POST.get('buyer', bom.buyer).strip()
            bom.date = request.POST.get('date') or None
            bom.notes = request.POST.get('notes', '').strip()
            bom.save()
            messages.success(request, 'BOM header updated.')

        return redirect('bom:shoe_bom_detail', slug=slug, bom_id=bom_id)

    colorways = bom.colorways.all()
    lines_by_category = {}
    for line in bom.bom_lines.select_related('colorway').order_by('category', 'position'):
        lines_by_category.setdefault(line.category, []).append(line)

    return render(request, 'bom/shoe_bom_detail.html', {
        'biz': biz,
        'bom': bom,
        'colorways': colorways,
        'lines_by_category': lines_by_category,
        'categories': ShoeBOMLine.CATEGORY,
    })
