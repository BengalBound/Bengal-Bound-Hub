from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hub.models import BusinessInstance, BusinessEmployee
from .models import CommissionRule, CommissionEntry


def _cm_check(slug, user, min_level=1):
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
def commission_home(request, slug):
    biz, emp, level = _cm_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    entries = CommissionEntry.objects.filter(business=biz).select_related('agent__user')
    total_gci = sum(e.gross_commission for e in entries)
    total_agent = sum(e.agent_amount for e in entries)
    total_broker = sum(e.broker_amount for e in entries)
    unpaid = entries.filter(is_paid=False)
    unpaid_total = sum(e.agent_amount for e in unpaid)

    stats = {
        'total_gci': total_gci,
        'total_agent': total_agent,
        'total_broker': total_broker,
        'unpaid_count': unpaid.count(),
        'unpaid_total': unpaid_total,
    }

    agents = BusinessEmployee.objects.filter(business=biz, is_active=True)
    agent_totals = {}
    for a in agents:
        agent_entries = entries.filter(agent=a)
        if agent_entries.exists():
            agent_totals[a] = {
                'gci': sum(e.gross_commission for e in agent_entries),
                'earned': sum(e.agent_amount for e in agent_entries),
                'count': agent_entries.count(),
            }

    rules = CommissionRule.objects.filter(business=biz, is_active=True)

    return render(request, 'commission/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats,
        'recent_entries': entries[:10], 'agent_totals': agent_totals, 'rules': rules,
    })


@login_required
def commission_list(request, slug):
    biz, emp, level = _cm_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    agents = BusinessEmployee.objects.filter(business=biz, is_active=True)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_entry':
            agent_id = request.POST.get('agent_id')
            agent = BusinessEmployee.objects.filter(pk=agent_id, business=biz).first() if agent_id else None
            gci = float(request.POST.get('gross_commission', 0))
            split = float(request.POST.get('agent_split_pct', 70))
            referral = float(request.POST.get('referral_amount', 0))
            agent_amount = round(gci * split / 100, 2)
            broker_amount = round(gci - agent_amount, 2)
            CommissionEntry.objects.create(
                business=biz,
                agent=agent,
                deal_reference=request.POST.get('deal_reference', ''),
                client_name=request.POST.get('client_name', ''),
                close_date=request.POST.get('close_date') or None,
                gross_commission=gci,
                agent_split_pct=split,
                agent_amount=agent_amount,
                broker_amount=broker_amount,
                referral_amount=referral,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Commission entry added.')
        elif action == 'mark_paid':
            entry = get_object_or_404(CommissionEntry, pk=request.POST.get('entry_id'), business=biz)
            entry.is_paid = True
            entry.paid_date = request.POST.get('paid_date') or None
            entry.save(update_fields=['is_paid', 'paid_date'])
            messages.success(request, 'Marked as paid.')
        elif action == 'add_rule':
            agent_id = request.POST.get('rule_agent_id')
            agent = BusinessEmployee.objects.filter(pk=agent_id, business=biz).first() if agent_id else None
            CommissionRule.objects.create(
                business=biz,
                name=request.POST.get('rule_name', ''),
                agent=agent,
                agent_split_pct=request.POST.get('agent_split_pct', 70),
                broker_split_pct=request.POST.get('broker_split_pct', 30),
                referral_fee_pct=request.POST.get('referral_fee_pct', 0),
                annual_cap=request.POST.get('annual_cap') or None,
                notes=request.POST.get('rule_notes', ''),
            )
            messages.success(request, 'Commission rule added.')
        return redirect('commission:list', slug=slug)

    entries = CommissionEntry.objects.filter(business=biz).select_related('agent__user')
    agent_filter = request.GET.get('agent', '')
    paid_filter = request.GET.get('paid', '')
    if agent_filter:
        entries = entries.filter(agent_id=agent_filter)
    if paid_filter == 'unpaid':
        entries = entries.filter(is_paid=False)
    elif paid_filter == 'paid':
        entries = entries.filter(is_paid=True)

    rules = CommissionRule.objects.filter(business=biz, is_active=True)

    return render(request, 'commission/list.html', {
        'biz': biz, 'access_level': level, 'entries': entries, 'rules': rules,
        'agents': agents, 'agent_filter': agent_filter, 'paid_filter': paid_filter,
    })
