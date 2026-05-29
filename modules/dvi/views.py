from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from hub.views import _get_business_for_user
from hub.access import get_access_level
from .models import InspectionTemplate, VehicleInspection, InspectionItem, DEFAULT_CHECKPOINTS


def _dvi_check(slug, user, min_level=2):
    biz = _get_business_for_user(slug, user)
    if not biz:
        return None, HttpResponseForbidden()
    if get_access_level(biz, user) < min_level:
        return None, HttpResponseForbidden()
    return biz, None


def _next_inspection_number(business):
    last = VehicleInspection.objects.filter(business=business).order_by('-pk').first()
    num = int(last.inspection_number) + 1 if last else 1
    return str(num).zfill(5)


@login_required(login_url='/accounts/login/')
def dvi_home(request, slug):
    biz, err = _dvi_check(slug, request.user)
    if err:
        return err

    recent = VehicleInspection.objects.filter(business=biz).select_related('performed_by', 'template')[:10]
    templates = InspectionTemplate.objects.filter(business=biz, is_active=True)

    result_counts = {}
    for r, _ in VehicleInspection.OVERALL:
        result_counts[r] = VehicleInspection.objects.filter(business=biz, overall_result=r).count()

    return render(request, 'dvi/home.html', {
        'biz': biz,
        'recent': recent,
        'templates': templates,
        'result_counts': result_counts,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def inspection_create(request, slug):
    biz, err = _dvi_check(slug, request.user, min_level=3)
    if err:
        return err

    templates = InspectionTemplate.objects.filter(business=biz, is_active=True)

    if request.method == 'POST':
        template_id = request.POST.get('template_id', '')
        template = None
        checkpoints = []

        if template_id:
            template = get_object_or_404(InspectionTemplate, pk=int(template_id), business=biz)
            checkpoints = template.checkpoints
        else:
            checkpoints = DEFAULT_CHECKPOINTS

        from hub.models import BusinessEmployee
        emp_id = request.POST.get('performed_by_id', '')

        inspection = VehicleInspection.objects.create(
            business=biz,
            inspection_number=_next_inspection_number(biz),
            template=template,
            vehicle_reg=request.POST.get('vehicle_reg', '').strip().upper(),
            vehicle_make=request.POST.get('vehicle_make', '').strip(),
            vehicle_model=request.POST.get('vehicle_model', '').strip(),
            vehicle_year=request.POST.get('vehicle_year', '') or None,
            vin=request.POST.get('vin', '').strip(),
            mileage=request.POST.get('mileage', '') or None,
            colour=request.POST.get('colour', '').strip(),
            customer_name=request.POST.get('customer_name', '').strip(),
            customer_phone=request.POST.get('customer_phone', '').strip(),
            customer_email=request.POST.get('customer_email', '').strip(),
            job_card_number=request.POST.get('job_card_number', '').strip(),
            overall_result='incomplete',
            performed_by_id=int(emp_id) if emp_id else None,
            notes=request.POST.get('notes', '').strip(),
        )

        for i, cp in enumerate(checkpoints):
            InspectionItem.objects.create(
                inspection=inspection,
                checkpoint=cp,
                status='ok',
                order=i,
            )

        messages.success(request, f"Inspection DVI-{inspection.inspection_number} created.")
        return redirect('dvi:inspection_detail', slug=slug, inspection_id=inspection.pk)

    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'dvi/inspection_form.html', {
        'biz': biz,
        'templates': templates,
        'employees': employees,
        'default_count': len(DEFAULT_CHECKPOINTS),
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def inspection_detail(request, slug, inspection_id):
    biz, err = _dvi_check(slug, request.user)
    if err:
        return err

    inspection = get_object_or_404(VehicleInspection, pk=inspection_id, business=biz)
    level = get_access_level(biz, request.user)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'update_items' and level >= 3:
            items = inspection.items.all()
            for item in items:
                status_key = f"status_{item.pk}"
                notes_key = f"notes_{item.pk}"
                item.status = request.POST.get(status_key, item.status)
                item.notes = request.POST.get(notes_key, '').strip()
                item.save(update_fields=['status', 'notes'])

            # Auto-determine overall result
            critical = inspection.items.filter(status='critical').exists()
            attention = inspection.items.filter(status='attention').exists()
            incomplete = inspection.items.filter(status='ok').count() == 0
            if critical:
                inspection.overall_result = 'fail'
            elif attention:
                inspection.overall_result = 'advisory'
            elif incomplete:
                inspection.overall_result = 'incomplete'
            else:
                inspection.overall_result = 'pass'
            inspection.save(update_fields=['overall_result'])
            messages.success(request, "Inspection updated.")

        elif action == 'override_result' and level >= 4:
            inspection.overall_result = request.POST.get('overall_result', inspection.overall_result)
            inspection.notes = request.POST.get('notes', inspection.notes).strip()
            inspection.save(update_fields=['overall_result', 'notes'])
            messages.success(request, "Result overridden.")

        elif action == 'generate_link' and level >= 3:
            inspection.generate_share_token()
            messages.success(request, "Shareable report link generated.")

        elif action == 'mark_sent' and level >= 3:
            inspection.report_sent = True
            inspection.save(update_fields=['report_sent'])
            messages.success(request, "Report marked as sent.")

        return redirect('dvi:inspection_detail', slug=slug, inspection_id=inspection_id)

    items = inspection.items.all()

    return render(request, 'dvi/inspection_detail.html', {
        'biz': biz,
        'inspection': inspection,
        'items': items,
        'item_statuses': InspectionItem.STATUS,
        'overall_choices': VehicleInspection.OVERALL,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


def inspection_report_public(request, token):
    """Public shareable report — no login required."""
    inspection = get_object_or_404(VehicleInspection, share_token=token)
    items = inspection.items.all()
    return render(request, 'dvi/inspection_report_public.html', {
        'inspection': inspection,
        'items': items,
    })


@login_required(login_url='/accounts/login/')
def template_list(request, slug):
    biz, err = _dvi_check(slug, request.user, min_level=4)
    if err:
        return err

    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        if action == 'create':
            raw = request.POST.get('checkpoints', '')
            checkpoints = [c.strip() for c in raw.splitlines() if c.strip()]
            if not checkpoints:
                checkpoints = DEFAULT_CHECKPOINTS
            InspectionTemplate.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', '').strip(),
                checkpoints=checkpoints,
            )
            messages.success(request, "Template created.")
        elif action == 'toggle':
            tpl_id = request.POST.get('template_id', '')
            if tpl_id:
                tpl = get_object_or_404(InspectionTemplate, pk=int(tpl_id), business=biz)
                tpl.is_active = not tpl.is_active
                tpl.save(update_fields=['is_active'])
        return redirect('dvi:templates', slug=slug)

    templates = InspectionTemplate.objects.filter(business=biz)
    return render(request, 'dvi/templates.html', {
        'biz': biz,
        'templates': templates,
        'default_checkpoints': DEFAULT_CHECKPOINTS,
        'is_owner': biz.owner == request.user,
    })
