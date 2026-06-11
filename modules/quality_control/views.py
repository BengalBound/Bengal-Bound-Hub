from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import InspectionTemplate, InspectionCriterion, Inspection, InspectionResult, NonConformance, ShoeDefectRecord


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    inspections = Inspection.objects.filter(business=biz)
    stats = {
        'pending': inspections.filter(result='pending').count(),
        'passed': inspections.filter(result='pass').count(),
        'failed': inspections.filter(result='fail').count(),
        'open_ncrs': NonConformance.objects.filter(business=biz, status__in=['open', 'in_review']).count(),
    }
    recent = inspections.order_by('-created_at')[:10]
    return render(request, 'quality_control/index.html', {
        'biz': biz, 'stats': stats, 'recent_inspections': recent,
    })


@login_required(login_url='/accounts/login/')
def inspections(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    result_filter = request.GET.get('result', '')
    qs = Inspection.objects.filter(business=biz).select_related('template', 'inspector').order_by('-scheduled_date')
    if result_filter:
        qs = qs.filter(result=result_filter)
    templates = InspectionTemplate.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Inspection.objects.create(
                business=biz,
                inspection_type=request.POST.get('inspection_type', 'final'),
                reference=request.POST.get('reference', '').strip(),
                lot_number=request.POST.get('lot_number', '').strip(),
                quantity=request.POST.get('quantity') or None,
                inspector=request.user,
                scheduled_date=request.POST.get('scheduled_date') or timezone.now().date(),
                template_id=request.POST.get('template') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Inspection created.')
        return redirect('quality_control:inspections', slug=slug)
    return render(request, 'quality_control/inspections.html', {
        'biz': biz, 'inspections': qs, 'templates': templates, 'result_filter': result_filter,
    })


@login_required(login_url='/accounts/login/')
def inspection_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    inspection = get_object_or_404(Inspection, pk=pk, business=biz)
    results = inspection.results.select_related('criterion')
    ncrs = inspection.nonconformances.all()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'record_result':
            criterion_name = request.POST.get('criterion_name', '').strip()
            InspectionResult.objects.create(
                inspection=inspection,
                criterion_name=criterion_name,
                result=request.POST.get('result', 'pass'),
                value=request.POST.get('value', '').strip(),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Result recorded.')
        elif action == 'complete':
            inspection.result = request.POST.get('result', 'pass')
            inspection.completed_date = timezone.now().date()
            inspection.notes = request.POST.get('notes', inspection.notes)
            inspection.save(update_fields=['result', 'completed_date', 'notes'])
            messages.success(request, f'Inspection marked as {inspection.get_result_display()}.')
        elif action == 'raise_ncr':
            NonConformance.objects.create(
                business=biz,
                inspection=inspection,
                title=request.POST.get('title', '').strip(),
                description=request.POST.get('description', ''),
                severity=request.POST.get('severity', 'minor'),
                created_by=request.user,
            )
            messages.success(request, 'Non-conformance raised.')
        return redirect('quality_control:inspection_detail', slug=slug, pk=pk)
    return render(request, 'quality_control/inspection_detail.html', {
        'biz': biz, 'inspection': inspection, 'results': results, 'ncrs': ncrs,
    })


@login_required(login_url='/accounts/login/')
def nonconformances(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status_filter = request.GET.get('status', '')
    qs = NonConformance.objects.filter(business=biz).select_related('assigned_to', 'created_by').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    if request.method == 'POST':
        action = request.POST.get('action')
        ncr = get_object_or_404(NonConformance, pk=request.POST.get('ncr_id'), business=biz)
        if action == 'update':
            ncr.status = request.POST.get('status', ncr.status)
            ncr.root_cause = request.POST.get('root_cause', ncr.root_cause)
            ncr.corrective_action = request.POST.get('corrective_action', ncr.corrective_action)
            if ncr.status == 'resolved' and not ncr.resolved_at:
                ncr.resolved_at = timezone.now()
            ncr.save()
            messages.success(request, 'NCR updated.')
        return redirect('quality_control:nonconformances', slug=slug)
    return render(request, 'quality_control/nonconformances.html', {
        'biz': biz, 'ncrs': qs, 'status_filter': status_filter,
    })


@login_required(login_url='/accounts/login/')
def qc_templates(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            tpl = InspectionTemplate.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', ''),
                created_by=request.user,
            )
            for i in range(1, 11):
                crit_name = request.POST.get(f'criterion_{i}', '').strip()
                if crit_name:
                    InspectionCriterion.objects.create(
                        template=tpl,
                        name=crit_name,
                        criterion_type=request.POST.get(f'criterion_type_{i}', 'pass_fail'),
                        position=i,
                    )
            messages.success(request, f'Template "{tpl.name}" created.')
        elif action == 'delete':
            InspectionTemplate.objects.filter(pk=request.POST.get('template_id'), business=biz).delete()
            messages.success(request, 'Template deleted.')
        return redirect('quality_control:qc_templates', slug=slug)
    all_templates = InspectionTemplate.objects.filter(business=biz).prefetch_related('criteria')
    return render(request, 'quality_control/qc_templates.html', {'biz': biz, 'templates': all_templates})


# ── Shoe Defect Log ───────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def shoe_defect_log(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    if request.method == 'POST':
        ShoeDefectRecord.objects.create(
            business=biz,
            inspection_stage=request.POST.get('inspection_stage', ''),
            inspection_date=request.POST.get('inspection_date') or timezone.now().date(),
            article_code=request.POST.get('article_code', '').strip(),
            lot_reference=request.POST.get('lot_reference', '').strip(),
            pairs_inspected=request.POST.get('pairs_inspected', 0) or 0,
            pairs_affected=request.POST.get('pairs_affected', 0) or 0,
            defect_description=request.POST.get('defect_description', '').strip(),
            severity=request.POST.get('severity', 'minor'),
            aql_level=request.POST.get('aql_level', ''),
            root_cause=request.POST.get('root_cause', '').strip(),
            corrective_action=request.POST.get('corrective_action', '').strip(),
            peel_test_result=request.POST.get('peel_test_result') or None,
            recorded_by=request.user,
        )
        messages.success(request, 'Defect record logged.')
        return redirect('quality_control:shoe_defect_log', slug=slug)

    stage_filter = request.GET.get('stage', '')
    severity_filter = request.GET.get('severity', '')
    records = ShoeDefectRecord.objects.filter(business=biz).select_related('recorded_by')
    if stage_filter:
        records = records.filter(inspection_stage=stage_filter)
    if severity_filter:
        records = records.filter(severity=severity_filter)

    return render(request, 'quality_control/shoe_defect_log.html', {
        'biz': biz,
        'records': records,
        'stage_filter': stage_filter,
        'severity_filter': severity_filter,
        'stages': ShoeDefectRecord.STAGE,
        'severities': ShoeDefectRecord.SEVERITY,
        'aql_levels': ShoeDefectRecord.AQL_LEVEL,
    })
