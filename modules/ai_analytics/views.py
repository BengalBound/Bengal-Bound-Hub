from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import AnalyticsDataset, AIInsight, KPIMetric


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    insights = AIInsight.objects.filter(business=biz)
    recent_insights = insights.filter(status='generated').order_by('-created_at')[:8]
    kpis = KPIMetric.objects.filter(business=biz).order_by('-period_date')[:12]
    return render(request, 'ai_analytics/index.html', {
        'biz': biz,
        'total_datasets': AnalyticsDataset.objects.filter(business=biz, is_active=True).count(),
        'total_insights': insights.filter(status='generated').count(),
        'total_kpis': KPIMetric.objects.filter(business=biz).count(),
        'actionable': insights.filter(is_actionable=True, status='generated').count(),
        'recent_insights': recent_insights,
        'kpis': kpis,
    })


@login_required(login_url='/accounts/login/')
def datasets(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            AnalyticsDataset.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                source=request.POST.get('source', 'manual'),
                description=request.POST.get('description', ''),
                created_by=request.user,
            )
            messages.success(request, 'Dataset created.')
        elif action == 'delete':
            AnalyticsDataset.objects.filter(pk=request.POST.get('dataset_id'), business=biz).delete()
            messages.success(request, 'Dataset deleted.')
        return redirect('ai_analytics:datasets', slug=slug)
    all_datasets = AnalyticsDataset.objects.filter(business=biz)
    return render(request, 'ai_analytics/datasets.html', {'biz': biz, 'datasets': all_datasets})


@login_required(login_url='/accounts/login/')
def insights(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    type_filter = request.GET.get('type', '')
    qs = AIInsight.objects.filter(business=biz).order_by('-created_at')
    if type_filter:
        qs = qs.filter(insight_type=type_filter)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            AIInsight.objects.create(
                business=biz,
                insight_type=request.POST.get('insight_type', 'summary'),
                title=request.POST.get('title', '').strip(),
                summary=request.POST.get('summary', ''),
                status='generated',
                is_actionable=request.POST.get('is_actionable') == 'on',
            )
            messages.success(request, 'Insight added.')
        elif action == 'dismiss':
            insight = get_object_or_404(AIInsight, pk=request.POST.get('insight_id'), business=biz)
            insight.status = 'dismissed'
            insight.save(update_fields=['status'])
            messages.info(request, 'Insight dismissed.')
        return redirect('ai_analytics:insights', slug=slug)
    return render(request, 'ai_analytics/insights.html', {
        'biz': biz, 'insights': qs, 'type_filter': type_filter,
    })


@login_required(login_url='/accounts/login/')
def kpis(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    qs = KPIMetric.objects.filter(business=biz).order_by('-period_date', 'name')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            KPIMetric.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', ''),
                value=request.POST.get('value', 0) or 0,
                target=request.POST.get('target') or None,
                unit=request.POST.get('unit', '').strip(),
                period=request.POST.get('period', 'monthly'),
                period_date=request.POST.get('period_date') or timezone.now().date(),
                source_module=request.POST.get('source_module', '').strip(),
            )
            messages.success(request, 'KPI metric added.')
        elif action == 'delete':
            KPIMetric.objects.filter(pk=request.POST.get('kpi_id'), business=biz).delete()
            messages.success(request, 'KPI deleted.')
        return redirect('ai_analytics:kpis', slug=slug)
    return render(request, 'ai_analytics/kpis.html', {'biz': biz, 'kpis': qs})
