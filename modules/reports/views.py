from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import ReportDefinition, ReportRun, Dashboard


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    reports = ReportDefinition.objects.filter(business=biz)
    stats = {
        'total_reports': reports.count(),
        'dashboards': Dashboard.objects.filter(business=biz).count(),
        'runs_today': ReportRun.objects.filter(report__business=biz, started_at__date=timezone.now().date()).count(),
    }
    recent_runs = ReportRun.objects.filter(report__business=biz).select_related('report', 'run_by').order_by('-started_at')[:10]
    dashboards = Dashboard.objects.filter(business=biz)
    return render(request, 'reports/index.html', {
        'biz': biz, 'stats': stats, 'recent_runs': recent_runs, 'dashboards': dashboards,
    })


@login_required(login_url='/accounts/login/')
def report_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    qs = ReportDefinition.objects.filter(business=biz).select_related('created_by')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            ReportDefinition.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', ''),
                report_type=request.POST.get('report_type', 'tabular'),
                data_source=request.POST.get('data_source', 'custom'),
                created_by=request.user,
            )
            messages.success(request, 'Report definition created.')
        elif action == 'delete':
            ReportDefinition.objects.filter(pk=request.POST.get('report_id'), business=biz).delete()
            messages.success(request, 'Report deleted.')
        return redirect('reports:report_list', slug=slug)
    return render(request, 'reports/report_list.html', {'biz': biz, 'reports': qs})


@login_required(login_url='/accounts/login/')
def report_run(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    report = get_object_or_404(ReportDefinition, pk=pk, business=biz)
    runs = report.runs.order_by('-started_at')[:20]
    if request.method == 'POST':
        run = ReportRun.objects.create(
            report=report,
            status='running',
            run_by=request.user,
        )
        run.status = 'completed'
        run.completed_at = timezone.now()
        run.row_count = 0
        run.save(update_fields=['status', 'completed_at', 'row_count'])
        messages.success(request, f'Report "{report.name}" run completed.')
        return redirect('reports:report_run', slug=slug, pk=pk)
    return render(request, 'reports/report_run.html', {
        'biz': biz, 'report': report, 'runs': runs,
    })


@login_required(login_url='/accounts/login/')
def dashboards(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Dashboard.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', ''),
                is_default=request.POST.get('is_default') == 'on',
                created_by=request.user,
            )
            messages.success(request, 'Dashboard created.')
        elif action == 'delete':
            Dashboard.objects.filter(pk=request.POST.get('dashboard_id'), business=biz).delete()
            messages.success(request, 'Dashboard deleted.')
        return redirect('reports:dashboards', slug=slug)
    all_dashboards = Dashboard.objects.filter(business=biz)
    all_reports = ReportDefinition.objects.filter(business=biz)
    return render(request, 'reports/dashboards.html', {
        'biz': biz, 'dashboards': all_dashboards, 'reports': all_reports,
    })
