from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q, Sum, Count

from hub.views import _get_business_for_user
from .models import Lead, LeadSource, LeadActivity


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    leads = Lead.objects.filter(business=biz)
    stats = {
        'total': leads.count(), 'new': leads.filter(status='new').count(),
        'qualified': leads.filter(status='qualified').count(),
        'won': leads.filter(status='won').count(),
        'pipeline_value': leads.exclude(status__in=['won', 'lost', 'unqualified']).aggregate(s=Sum('estimated_value'))['s'] or 0,
    }
    by_status = leads.values('status').annotate(count=Count('id'))
    recent = leads.order_by('-created_at')[:10]
    return render(request, 'leads/index.html', {'biz': biz, 'stats': stats, 'by_status': by_status, 'recent_leads': recent})


@login_required(login_url='/accounts/login/')
def lead_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    qs = Lead.objects.filter(business=biz).select_related('source', 'assigned_to')
    if q:
        qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(company__icontains=q) | Q(email__icontains=q))
    if status:
        qs = qs.filter(status=status)
    sources = LeadSource.objects.filter(business=biz)
    return render(request, 'leads/lead_list.html', {'biz': biz, 'leads': qs, 'q': q, 'status_filter': status, 'sources': sources})


@login_required(login_url='/accounts/login/')
def lead_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    sources = LeadSource.objects.filter(business=biz)
    if request.method == 'POST':
        lead = Lead.objects.create(
            business=biz, first_name=request.POST.get('first_name', '').strip(),
            last_name=request.POST.get('last_name', '').strip(), company=request.POST.get('company', '').strip(),
            email=request.POST.get('email', '').strip(), phone=request.POST.get('phone', '').strip(),
            industry=request.POST.get('industry', ''), country=request.POST.get('country', ''),
            source_id=request.POST.get('source') or None,
            estimated_value=request.POST.get('estimated_value') or None,
            description=request.POST.get('description', ''),
            assigned_to=request.user, created_by=request.user,
        )
        messages.success(request, f'Lead "{lead}" created.')
        return redirect('leads:lead_detail', slug=slug, pk=lead.pk)
    return render(request, 'leads/lead_form.html', {'biz': biz, 'sources': sources})


@login_required(login_url='/accounts/login/')
def lead_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    lead = get_object_or_404(Lead, pk=pk, business=biz)
    activities = lead.activities.order_by('-created_at')
    sources = LeadSource.objects.filter(business=biz)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            for f in ['first_name', 'last_name', 'company', 'email', 'phone', 'industry', 'country', 'description', 'notes']:
                setattr(lead, f, request.POST.get(f, getattr(lead, f)))
            lead.status = request.POST.get('status', lead.status)
            lead.estimated_value = request.POST.get('estimated_value') or lead.estimated_value
            lead.source_id = request.POST.get('source') or lead.source_id
            lead.save()
            messages.success(request, 'Lead updated.')
        elif action == 'add_activity':
            LeadActivity.objects.create(
                lead=lead, activity_type=request.POST.get('activity_type', 'note'),
                title=request.POST.get('title', '').strip(), notes=request.POST.get('notes', ''),
                created_by=request.user,
            )
            messages.success(request, 'Activity logged.')
        elif action == 'delete':
            lead.delete()
            messages.success(request, 'Lead deleted.')
            return redirect('leads:lead_list', slug=slug)
        return redirect('leads:lead_detail', slug=slug, pk=pk)
    return render(request, 'leads/lead_detail.html', {'biz': biz, 'lead': lead, 'activities': activities, 'sources': sources})
