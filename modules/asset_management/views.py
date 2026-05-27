from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone

from hub.views import _get_business_for_user
from hub.access import get_access_level
from .models import Asset, AssetCategory, MaintenanceSchedule, WorkOrder, AssetDocument, AssetDepreciation


def _asset_check(slug, user, min_level=3):
    biz = _get_business_for_user(slug, user)
    if not biz:
        return None, HttpResponseForbidden()
    if get_access_level(biz, user) < min_level:
        return None, HttpResponseForbidden()
    return biz, None


@login_required(login_url='/accounts/login/')
def asset_dashboard(request, slug):
    biz, err = _asset_check(slug, request.user)
    if err:
        return err

    assets = Asset.objects.filter(business=biz)
    status_counts = {}
    for s, _ in Asset.STATUS:
        status_counts[s] = assets.filter(status=s).count()

    overdue_wos = WorkOrder.objects.filter(
        business=biz, status__in=['open', 'assigned', 'in_progress'],
        due_date__lt=timezone.localdate()
    ).count()

    recent_wos = WorkOrder.objects.filter(business=biz).select_related('asset').order_by('-created_at')[:5]

    return render(request, 'asset_management/dashboard.html', {
        'biz': biz,
        'total_assets': assets.count(),
        'status_counts': status_counts,
        'overdue_wos': overdue_wos,
        'recent_wos': recent_wos,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def asset_list(request, slug):
    biz, err = _asset_check(slug, request.user)
    if err:
        return err

    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    assets = Asset.objects.filter(business=biz).select_related('category', 'assigned_to')
    if status_filter:
        assets = assets.filter(status=status_filter)
    if category_filter:
        assets = assets.filter(category_id=category_filter)

    categories = AssetCategory.objects.filter(business=biz)
    return render(request, 'asset_management/asset_list.html', {
        'biz': biz,
        'assets': assets,
        'categories': categories,
        'statuses': Asset.STATUS,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def asset_create(request, slug):
    biz, err = _asset_check(slug, request.user, min_level=5)
    if err:
        return err

    if request.method == 'POST':
        from hub.models import BusinessEmployee
        cat_id = request.POST.get('category_id', '')
        emp_id = request.POST.get('assigned_to_id', '')
        purchase_date = request.POST.get('purchase_date', '') or None
        purchase_cost = request.POST.get('purchase_cost', '') or None
        warranty_expiry = request.POST.get('warranty_expiry', '') or None

        Asset.objects.create(
            business=biz,
            asset_tag=request.POST.get('asset_tag', '').strip(),
            name=request.POST.get('name', '').strip(),
            description=request.POST.get('description', '').strip(),
            category_id=int(cat_id) if cat_id else None,
            serial_number=request.POST.get('serial_number', '').strip(),
            manufacturer=request.POST.get('manufacturer', '').strip(),
            model_number=request.POST.get('model_number', '').strip(),
            location=request.POST.get('location', '').strip(),
            assigned_to_id=int(emp_id) if emp_id else None,
            status=request.POST.get('status', 'active'),
            condition=request.POST.get('condition', 'good'),
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            warranty_expiry=warranty_expiry,
        )
        messages.success(request, "Asset registered.")
        return redirect('asset_management:asset_list', slug=slug)

    from hub.models import BusinessEmployee
    categories = AssetCategory.objects.filter(business=biz)
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    return render(request, 'asset_management/asset_form.html', {
        'biz': biz,
        'categories': categories,
        'employees': employees,
        'statuses': Asset.STATUS,
        'conditions': Asset.CONDITION,
        'asset': None,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def asset_detail(request, slug, asset_id):
    biz, err = _asset_check(slug, request.user)
    if err:
        return err

    asset = get_object_or_404(Asset, pk=asset_id, business=biz)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'upload_doc':
            AssetDocument.objects.create(
                asset=asset,
                doc_type=request.POST.get('doc_type', 'other'),
                title=request.POST.get('title', '').strip(),
                file=request.FILES.get('file'),
                uploaded_by=request.user,
            )
            messages.success(request, "Document uploaded.")
        elif action == 'create_wo' and get_access_level(biz, request.user) >= 4:
            from hub.models import BusinessEmployee
            import random, string
            wo_num = 'WO-' + ''.join(random.choices(string.digits, k=6))
            emp_id = request.POST.get('assigned_to_id', '')
            due_date = request.POST.get('due_date', '') or None
            WorkOrder.objects.create(
                business=biz,
                asset=asset,
                wo_number=wo_num,
                title=request.POST.get('title', '').strip(),
                description=request.POST.get('description', '').strip(),
                work_type=request.POST.get('work_type', 'corrective'),
                priority=request.POST.get('priority', 'normal'),
                assigned_to_id=int(emp_id) if emp_id else None,
                due_date=due_date,
                created_by=request.user,
            )
            messages.success(request, "Work order created.")
        return redirect('asset_management:asset_detail', slug=slug, asset_id=asset_id)

    from hub.models import BusinessEmployee
    work_orders = asset.work_orders.all().order_by('-created_at')
    documents = asset.documents.all()
    depreciation = asset.depreciation_records.all()
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'asset_management/asset_detail.html', {
        'biz': biz,
        'asset': asset,
        'work_orders': work_orders,
        'documents': documents,
        'depreciation': depreciation,
        'employees': employees,
        'wo_types': WorkOrder.TYPES,
        'wo_priorities': WorkOrder.PRIORITY,
        'doc_types': AssetDocument.TYPES,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def asset_work_orders(request, slug):
    biz, err = _asset_check(slug, request.user)
    if err:
        return err

    status_filter = request.GET.get('status', '')
    wos = WorkOrder.objects.filter(business=biz).select_related('asset', 'assigned_to')
    if status_filter:
        wos = wos.filter(status=status_filter)

    if request.method == 'POST' and get_access_level(biz, request.user) >= 4:
        wo_id = request.POST.get('wo_id', '')
        new_status = request.POST.get('status', '')
        if wo_id and new_status:
            wo = get_object_or_404(WorkOrder, pk=int(wo_id), business=biz)
            wo.status = new_status
            if new_status == 'in_progress' and not wo.started_at:
                wo.started_at = timezone.now()
            elif new_status == 'completed' and not wo.completed_at:
                wo.completed_at = timezone.now()
                wo.resolution_notes = request.POST.get('resolution_notes', '').strip()
            wo.save()
            messages.success(request, "Work order updated.")
        return redirect('asset_management:work_orders', slug=slug)

    return render(request, 'asset_management/work_orders.html', {
        'biz': biz,
        'wos': wos,
        'statuses': WorkOrder.STATUS,
        'status_filter': status_filter,
        'today': timezone.localdate(),
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def asset_categories(request, slug):
    biz, err = _asset_check(slug, request.user, min_level=6)
    if err:
        return err

    if request.method == 'POST':
        AssetCategory.objects.create(
            business=biz,
            name=request.POST.get('name', '').strip(),
            code=request.POST.get('code', '').strip(),
            useful_life_years=int(request.POST.get('useful_life_years', 5)),
            depreciation_rate=request.POST.get('depreciation_rate', 20),
        )
        messages.success(request, "Category created.")
        return redirect('asset_management:categories', slug=slug)

    categories = AssetCategory.objects.filter(business=biz)
    return render(request, 'asset_management/categories.html', {
        'biz': biz,
        'categories': categories,
        'is_owner': biz.owner == request.user,
    })
