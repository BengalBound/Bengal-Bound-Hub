from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q, Sum

from hub.views import _get_business_for_user
from .models import Contact, Pipeline, Stage, Deal, Activity


def _biz(slug, user):
    return _get_business_for_user(slug, user)


def _ensure_default_pipeline(biz):
    pipeline, created = Pipeline.objects.get_or_create(
        business=biz, is_default=True,
        defaults={'name': 'Sales Pipeline'}
    )
    if created:
        defaults = [
            ('New', 0, 10, '#94a3b8'), ('Qualified', 1, 25, '#3b82f6'),
            ('Proposal', 2, 50, '#f59e0b'), ('Negotiation', 3, 75, '#8b5cf6'),
            ('Won', 4, 100, '#22c55e'), ('Lost', 5, 0, '#ef4444'),
        ]
        for name, pos, prob, color in defaults:
            Stage.objects.create(
                pipeline=pipeline, name=name, position=pos, probability=prob, color=color,
                is_won=(name == 'Won'), is_lost=(name == 'Lost')
            )
    return pipeline


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    pipeline = _ensure_default_pipeline(biz)
    stages = pipeline.stages.all()
    deals_qs = Deal.objects.filter(business=biz, is_lost=False)
    stats = {
        'total_contacts': Contact.objects.filter(business=biz).count(),
        'open_deals': deals_qs.filter(is_won=False).count(),
        'won_deals': deals_qs.filter(is_won=True).count(),
        'pipeline_value': deals_qs.filter(is_won=False).aggregate(v=Sum('amount'))['v'] or 0,
    }
    stages_data = []
    for stage in stages:
        stage_deals = deals_qs.filter(stage=stage, is_won=stage.is_won, is_lost=stage.is_lost)
        stages_data.append({'stage': stage, 'deals': stage_deals, 'count': stage_deals.count()})
    recent_activities = Activity.objects.filter(business=biz).select_related('contact', 'deal')[:10]
    return render(request, 'crm/index.html', {
        'biz': biz, 'stats': stats, 'stages_data': stages_data,
        'pipeline': pipeline, 'recent_activities': recent_activities,
    })


@login_required(login_url='/accounts/login/')
def contacts(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    q = request.GET.get('q', '')
    contact_type = request.GET.get('type', '')
    qs = Contact.objects.filter(business=biz)
    if q:
        qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q) | Q(company_name__icontains=q))
    if contact_type:
        qs = qs.filter(contact_type=contact_type)
    return render(request, 'crm/contacts.html', {'biz': biz, 'contacts': qs, 'q': q, 'contact_type': contact_type})


@login_required(login_url='/accounts/login/')
def contact_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    contact = get_object_or_404(Contact, pk=pk, business=biz)
    deals = contact.deals.filter(business=biz)
    activities = contact.activities.filter(business=biz).order_by('-created_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            for field in ['first_name', 'last_name', 'company_name', 'email', 'phone', 'mobile', 'job_title', 'industry', 'address', 'city', 'country', 'website', 'notes', 'tags']:
                setattr(contact, field, request.POST.get(field, getattr(contact, field)))
            contact.contact_type = request.POST.get('contact_type', contact.contact_type)
            contact.save()
            messages.success(request, 'Contact updated.')
            return redirect('crm:contact_detail', slug=slug, pk=pk)
        if action == 'delete':
            contact.delete()
            messages.success(request, 'Contact deleted.')
            return redirect('crm:contacts', slug=slug)
        if action == 'add_activity':
            Activity.objects.create(
                business=biz, contact=contact,
                activity_type=request.POST.get('activity_type', 'note'),
                title=request.POST.get('title', '').strip(),
                notes=request.POST.get('notes', ''),
                created_by=request.user, assigned_to=request.user,
            )
            messages.success(request, 'Activity logged.')
            return redirect('crm:contact_detail', slug=slug, pk=pk)
    return render(request, 'crm/contact_detail.html', {'biz': biz, 'contact': contact, 'deals': deals, 'activities': activities})


@login_required(login_url='/accounts/login/')
def contact_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        contact = Contact.objects.create(
            business=biz,
            contact_type=request.POST.get('contact_type', 'person'),
            first_name=request.POST.get('first_name', '').strip(),
            last_name=request.POST.get('last_name', '').strip(),
            company_name=request.POST.get('company_name', '').strip(),
            email=request.POST.get('email', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            mobile=request.POST.get('mobile', '').strip(),
            job_title=request.POST.get('job_title', '').strip(),
            industry=request.POST.get('industry', '').strip(),
            address=request.POST.get('address', '').strip(),
            city=request.POST.get('city', '').strip(),
            country=request.POST.get('country', '').strip(),
            notes=request.POST.get('notes', '').strip(),
            created_by=request.user, owner=request.user,
        )
        messages.success(request, f'Contact "{contact}" created.')
        return redirect('crm:contact_detail', slug=slug, pk=contact.pk)
    return render(request, 'crm/contact_form.html', {'biz': biz})


@login_required(login_url='/accounts/login/')
def deals(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    pipeline = _ensure_default_pipeline(biz)
    stages = pipeline.stages.prefetch_related('deals').all()
    qs = Deal.objects.filter(business=biz).select_related('contact', 'stage')
    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(contact__first_name__icontains=q) | Q(contact__company_name__icontains=q))
    return render(request, 'crm/deals.html', {'biz': biz, 'deals': qs, 'stages': stages, 'pipeline': pipeline, 'q': q})


@login_required(login_url='/accounts/login/')
def deal_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    pipeline = _ensure_default_pipeline(biz)
    if request.method == 'POST':
        stage_id = request.POST.get('stage')
        contact_id = request.POST.get('contact') or None
        deal = Deal.objects.create(
            business=biz,
            name=request.POST.get('name', '').strip() or 'New Deal',
            pipeline=pipeline,
            stage=get_object_or_404(Stage, pk=stage_id, pipeline=pipeline) if stage_id else pipeline.stages.first(),
            contact_id=contact_id,
            amount=request.POST.get('amount') or 0,
            priority=request.POST.get('priority', 'normal'),
            expected_close=request.POST.get('expected_close') or None,
            description=request.POST.get('description', '').strip(),
            created_by=request.user, owner=request.user,
        )
        messages.success(request, f'Deal "{deal.name}" created.')
        return redirect('crm:deals', slug=slug)
    contacts_qs = Contact.objects.filter(business=biz)
    stages = pipeline.stages.all()
    return render(request, 'crm/deal_form.html', {'biz': biz, 'contacts': contacts_qs, 'stages': stages, 'pipeline': pipeline})


@login_required(login_url='/accounts/login/')
def deal_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    deal = get_object_or_404(Deal, pk=pk, business=biz)
    pipeline = deal.pipeline
    stages = pipeline.stages.all() if pipeline else []
    activities = deal.activities.order_by('-created_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            deal.name = request.POST.get('name', deal.name).strip() or deal.name
            deal.amount = request.POST.get('amount', deal.amount)
            deal.priority = request.POST.get('priority', deal.priority)
            deal.expected_close = request.POST.get('expected_close') or None
            deal.description = request.POST.get('description', deal.description)
            stage_id = request.POST.get('stage')
            if stage_id:
                deal.stage = get_object_or_404(Stage, pk=stage_id, pipeline=pipeline)
            deal.save()
            messages.success(request, 'Deal updated.')
        elif action == 'won':
            deal.is_won = True; deal.is_lost = False
            deal.stage = pipeline.stages.filter(is_won=True).first()
            deal.save()
            messages.success(request, 'Deal marked as Won!')
        elif action == 'lost':
            deal.is_lost = True; deal.is_won = False
            deal.lost_reason = request.POST.get('lost_reason', '')
            deal.stage = pipeline.stages.filter(is_lost=True).first()
            deal.save()
            messages.info(request, 'Deal marked as Lost.')
        elif action == 'reopen':
            deal.is_won = False; deal.is_lost = False
            deal.stage = pipeline.stages.filter(is_won=False, is_lost=False).first()
            deal.save()
            messages.info(request, 'Deal reopened.')
        elif action == 'add_activity':
            Activity.objects.create(
                business=biz, deal=deal,
                activity_type=request.POST.get('activity_type', 'note'),
                title=request.POST.get('title', '').strip(),
                notes=request.POST.get('notes', ''),
                created_by=request.user, assigned_to=request.user,
            )
            messages.success(request, 'Activity logged.')
        elif action == 'delete':
            deal.delete()
            messages.success(request, 'Deal deleted.')
            return redirect('crm:deals', slug=slug)
        return redirect('crm:deal_detail', slug=slug, pk=pk)
    return render(request, 'crm/deal_detail.html', {'biz': biz, 'deal': deal, 'stages': stages, 'activities': activities})


@login_required(login_url='/accounts/login/')
@require_POST
def deal_move(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    deal = get_object_or_404(Deal, pk=pk, business=biz)
    stage_id = request.POST.get('stage_id')
    stage = get_object_or_404(Stage, pk=stage_id, pipeline__business=biz)
    deal.stage = stage
    deal.is_won = stage.is_won
    deal.is_lost = stage.is_lost
    deal.save(update_fields=['stage', 'is_won', 'is_lost'])
    return JsonResponse({'ok': True, 'stage': stage.name})


@login_required(login_url='/accounts/login/')
def activities(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    qs = Activity.objects.filter(business=biz).select_related('contact', 'deal', 'assigned_to')
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
    return render(request, 'crm/activities.html', {'biz': biz, 'activities': qs, 'status': status})


@login_required
def export_contacts_csv(request, slug):
    """Export all CRM contacts for this business as CSV."""
    from core.exports import crm_contacts_csv
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    contacts = Contact.objects.filter(business=biz).order_by('first_name', 'last_name')
    return crm_contacts_csv(contacts)


@login_required
def export_deals_csv(request, slug):
    """Export all CRM deals for this business as CSV."""
    from core.exports import crm_deals_csv
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    deals = Deal.objects.filter(
        stage__pipeline__business=biz
    ).select_related('stage__pipeline', 'contact').order_by('-created_at')
    return crm_deals_csv(deals)
