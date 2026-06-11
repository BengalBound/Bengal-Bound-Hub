from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from hub.models import BusinessInstance, BusinessEmployee
from .models import Deal, DealDocument, DealNote, DealMilestone


def _df_check(slug, user, min_level=1):
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
def deal_home(request, slug):
    biz, emp, level = _df_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    deals = Deal.objects.filter(business=biz)
    pipeline = {}
    for stage_key, stage_label in Deal.STAGES:
        stage_deals = deals.filter(stage=stage_key)
        pipeline[stage_key] = {
            'label': stage_label,
            'count': stage_deals.count(),
            'value': sum(d.offer_price or d.listing_price or 0 for d in stage_deals),
        }

    active_deals = deals.exclude(stage__in=['closed', 'dead'])
    total_pipeline_value = sum(d.offer_price or d.listing_price or 0 for d in active_deals)
    pending_gci = sum(d.gross_commission or 0 for d in active_deals if d.gross_commission)

    stats = {
        'total': deals.count(),
        'active': active_deals.count(),
        'closed': deals.filter(stage='closed').count(),
        'pipeline_value': total_pipeline_value,
        'pending_gci': pending_gci,
    }

    return render(request, 'deal_flow/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats,
        'pipeline': pipeline, 'recent_deals': deals[:8],
    })


@login_required
def deal_list(request, slug):
    biz, emp, level = _df_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    deals = Deal.objects.filter(business=biz).select_related('assigned_agent__user')
    stage_filter = request.GET.get('stage', '')
    agent_filter = request.GET.get('agent', '')

    if stage_filter:
        deals = deals.filter(stage=stage_filter)
    if agent_filter:
        deals = deals.filter(assigned_agent_id=agent_filter)

    agents = BusinessEmployee.objects.filter(business=biz, is_active=True)
    return render(request, 'deal_flow/deal_list.html', {
        'biz': biz, 'access_level': level, 'deals': deals,
        'stage_filter': stage_filter, 'agent_filter': agent_filter,
        'stages': Deal.STAGES, 'agents': agents,
    })


@login_required
def deal_add(request, slug):
    biz, emp, level = _df_check(slug, request.user, min_level=2)
    if not level:
        return redirect('deal_flow:deal_list', slug=slug)

    agents = BusinessEmployee.objects.filter(business=biz, is_active=True)

    if request.method == 'POST':
        agent_id = request.POST.get('assigned_agent_id')
        agent = BusinessEmployee.objects.filter(pk=agent_id, business=biz).first() if agent_id else emp
        deal = Deal.objects.create(
            business=biz,
            title=request.POST.get('title', ''),
            property_address=request.POST.get('property_address', ''),
            client_name=request.POST.get('client_name', ''),
            client_email=request.POST.get('client_email', ''),
            client_phone=request.POST.get('client_phone', ''),
            deal_type=request.POST.get('deal_type', 'purchase'),
            stage=request.POST.get('stage', 'prospect'),
            assigned_agent=agent,
            listing_price=request.POST.get('listing_price') or None,
            offer_price=request.POST.get('offer_price') or None,
            commission_pct=request.POST.get('commission_pct') or None,
            expected_close_date=request.POST.get('expected_close_date') or None,
            notes=request.POST.get('notes', ''),
        )
        # Seed default document checklist
        defaults = ['Purchase Agreement', 'Seller Disclosure', 'Home Inspection Report',
                    'Title / Deed Search', 'Mortgage Pre-Approval', 'Closing Statement']
        for doc in defaults:
            DealDocument.objects.create(deal=deal, document_name=doc, is_required=True)
        messages.success(request, f'Deal "{deal.title}" created.')
        return redirect('deal_flow:deal_detail', slug=slug, deal_id=deal.pk)

    return render(request, 'deal_flow/deal_form.html', {
        'biz': biz, 'access_level': level, 'agents': agents,
        'deal_types': Deal.DEAL_TYPES, 'stages': Deal.STAGES,
    })


@login_required
def deal_detail(request, slug, deal_id):
    biz, emp, level = _df_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    deal = get_object_or_404(Deal, pk=deal_id, business=biz)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_stage' and level >= 2:
            new_stage = request.POST.get('stage')
            if new_stage in dict(Deal.STAGES):
                deal.stage = new_stage
                if new_stage == 'closed':
                    deal.actual_close_date = timezone.now().date()
                deal.save(update_fields=['stage', 'actual_close_date'])
                messages.success(request, f'Stage moved to {deal.get_stage_display()}.')

        elif action == 'add_document' and level >= 2:
            DealDocument.objects.create(
                deal=deal,
                document_name=request.POST.get('document_name', ''),
                is_required='is_required' in request.POST,
                file_url=request.POST.get('file_url', ''),
                notes=request.POST.get('notes', ''),
            )

        elif action == 'update_doc' and level >= 2:
            doc = get_object_or_404(DealDocument, pk=request.POST.get('doc_id'), deal=deal)
            doc.status = request.POST.get('status', doc.status)
            doc.file_url = request.POST.get('file_url', doc.file_url)
            if doc.status == 'uploaded' and not doc.uploaded_at:
                doc.uploaded_at = timezone.now()
                doc.uploaded_by = emp
            doc.save()

        elif action == 'add_note':
            DealNote.objects.create(deal=deal, content=request.POST.get('content', ''), created_by=emp)  # noqa: deal_notes

        elif action == 'add_milestone' and level >= 2:
            DealMilestone.objects.create(
                deal=deal,
                name=request.POST.get('name', ''),
                due_date=request.POST.get('due_date') or None,
            )

        elif action == 'complete_milestone':
            ms = get_object_or_404(DealMilestone, pk=request.POST.get('milestone_id'), deal=deal)
            ms.is_done = True
            ms.completed_at = timezone.now()
            ms.save(update_fields=['is_done', 'completed_at'])

        elif action == 'broker_review' and level >= 3:
            deal.broker_approved = 'approved' in request.POST.get('review_action', '')
            deal.broker_notes = request.POST.get('broker_notes', '')
            deal.save(update_fields=['broker_approved', 'broker_notes'])
            messages.success(request, 'Broker review saved.')

        return redirect('deal_flow:deal_detail', slug=slug, deal_id=deal_id)

    docs = deal.documents.all()
    notes = deal.deal_notes.all()
    milestones = deal.milestones.all()
    docs_complete = docs.filter(status='approved').count()
    docs_total = docs.count()

    return render(request, 'deal_flow/deal_detail.html', {
        'biz': biz, 'access_level': level, 'deal': deal,
        'docs': docs, 'notes': notes, 'milestones': milestones,
        'docs_complete': docs_complete, 'docs_total': docs_total,
        'stages': Deal.STAGES, 'doc_statuses': DealDocument.DOC_STATUS,
    })
