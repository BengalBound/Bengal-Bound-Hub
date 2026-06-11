from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hub.models import BusinessInstance, BusinessEmployee
from .models import StoreLayout, PlanogramSection, PlanogramSlot


def _pg_check(slug, user, min_level=1):
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
def planogram_home(request, slug):
    biz, emp, level = _pg_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'create_layout':
            StoreLayout.objects.create(
                business=biz,
                name=request.POST.get('name', ''),
                store_location=request.POST.get('store_location', ''),
                description=request.POST.get('description', ''),
                created_by=emp,
            )
            messages.success(request, 'Layout created.')
        elif action == 'toggle_layout':
            layout = get_object_or_404(StoreLayout, pk=request.POST.get('layout_id'), business=biz)
            layout.is_active = not layout.is_active
            layout.save(update_fields=['is_active'])
        return redirect('planogram:home', slug=slug)

    layouts = StoreLayout.objects.filter(business=biz)
    total_slots = sum(l.slot_count for l in layouts)
    reorder_alerts = PlanogramSlot.objects.filter(
        section__layout__business=biz
    ).select_related('section__layout')
    reorder_count = sum(1 for s in reorder_alerts if s.needs_reorder)

    return render(request, 'planogram/home.html', {
        'biz': biz, 'access_level': level, 'layouts': layouts,
        'total_slots': total_slots, 'reorder_count': reorder_count,
    })


@login_required
def layout_detail(request, slug, layout_id):
    biz, emp, level = _pg_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    layout = get_object_or_404(StoreLayout, pk=layout_id, business=biz)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_section':
            PlanogramSection.objects.create(
                layout=layout,
                name=request.POST.get('section_name', ''),
                display_order=request.POST.get('display_order', 0),
            )
            messages.success(request, 'Section added.')
        elif action == 'add_slot':
            section = get_object_or_404(PlanogramSection, pk=request.POST.get('section_id'), layout=layout)
            PlanogramSlot.objects.create(
                section=section,
                product_name=request.POST.get('product_name', ''),
                sku=request.POST.get('sku', ''),
                shelf_number=request.POST.get('shelf_number', ''),
                position=request.POST.get('position', ''),
                facings=request.POST.get('facings', 1),
                min_stock=request.POST.get('min_stock') or None,
                current_stock=request.POST.get('current_stock') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Product slot added.')
        elif action == 'update_stock':
            slot = get_object_or_404(PlanogramSlot, pk=request.POST.get('slot_id'), section__layout=layout)
            slot.current_stock = request.POST.get('current_stock') or None
            slot.save(update_fields=['current_stock'])
        elif action == 'delete_slot':
            PlanogramSlot.objects.filter(pk=request.POST.get('slot_id'), section__layout=layout).delete()
        elif action == 'delete_section':
            PlanogramSection.objects.filter(pk=request.POST.get('section_id'), layout=layout).delete()
        return redirect('planogram:layout_detail', slug=slug, layout_id=layout_id)

    sections = layout.sections.prefetch_related('slots').all()
    all_slots = PlanogramSlot.objects.filter(section__layout=layout)
    reorder_slots = [s for s in all_slots if s.needs_reorder]

    return render(request, 'planogram/layout_detail.html', {
        'biz': biz, 'access_level': level, 'layout': layout,
        'sections': sections, 'reorder_slots': reorder_slots,
    })
