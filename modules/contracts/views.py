from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from hub.views import _get_business_for_user
from .models import Contract, ContractTemplate, ContractParty


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    contracts = Contract.objects.filter(business=biz)
    today = timezone.now().date()
    soon = today + timedelta(days=30)
    recent = contracts.order_by('-created_at')[:10]
    return render(request, 'contracts/index.html', {
        'biz': biz,
        'total_contracts': contracts.count(),
        'active_contracts': contracts.filter(status='signed').count(),
        'expiring_soon': contracts.filter(status='signed', valid_until__lte=soon, valid_until__gte=today).count(),
        'expired_contracts': contracts.filter(status='expired').count(),
        'recent_contracts': recent,
    })


@login_required(login_url='/accounts/login/')
def contract_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status_filter = request.GET.get('status', '')
    qs = Contract.objects.filter(business=biz).select_related('created_by').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'contracts/contract_list.html', {
        'biz': biz, 'contracts': qs, 'status_filter': status_filter,
    })


@login_required(login_url='/accounts/login/')
def contract_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    templates = ContractTemplate.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        template_id = request.POST.get('template')
        content = request.POST.get('content', '').strip()
        if template_id and not content:
            tpl = ContractTemplate.objects.filter(pk=template_id, business=biz).first()
            if tpl:
                content = tpl.content
        count = Contract.objects.filter(business=biz).count() + 1
        contract = Contract.objects.create(
            business=biz,
            title=request.POST.get('title', '').strip(),
            reference=f"CTR-{count:04d}",
            content=content,
            template_id=template_id or None,
            valid_from=request.POST.get('valid_from') or timezone.now().date(),
            valid_until=request.POST.get('valid_until') or None,
            value=request.POST.get('value') or None,
            currency=request.POST.get('currency', 'USD').strip(),
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        for i in range(1, 6):
            name = request.POST.get(f'party_name_{i}', '').strip()
            if name:
                ContractParty.objects.create(
                    contract=contract,
                    role=request.POST.get(f'party_role_{i}', 'signer'),
                    name=name,
                    email=request.POST.get(f'party_email_{i}', '').strip(),
                    company=request.POST.get(f'party_company_{i}', '').strip(),
                )
        messages.success(request, f'Contract "{contract.title}" created.')
        return redirect('contracts:contract_detail', slug=slug, pk=contract.pk)
    return render(request, 'contracts/contract_form.html', {
        'biz': biz, 'templates': templates,
    })


@login_required(login_url='/accounts/login/')
def contract_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    contract = get_object_or_404(Contract, pk=pk, business=biz)
    parties = contract.parties.all()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            contract.status = request.POST.get('status', contract.status)
            contract.save(update_fields=['status'])
            messages.success(request, f'Contract status updated to {contract.get_status_display()}.')
        elif action == 'add_party':
            ContractParty.objects.create(
                contract=contract,
                role=request.POST.get('role', 'signer'),
                name=request.POST.get('name', '').strip(),
                email=request.POST.get('email', '').strip(),
                company=request.POST.get('company', '').strip(),
            )
            messages.success(request, 'Party added.')
        elif action == 'sign':
            party = get_object_or_404(ContractParty, pk=request.POST.get('party_id'), contract=contract)
            party.signed_at = timezone.now()
            party.signature_data = request.POST.get('signature_data', '')
            party.ip_address = request.META.get('REMOTE_ADDR')
            party.save(update_fields=['signed_at', 'signature_data', 'ip_address'])
            all_signed = all(p.signed_at for p in contract.parties.filter(role='signer'))
            if all_signed:
                contract.status = 'signed'
                contract.save(update_fields=['status'])
            messages.success(request, 'Signed successfully.')
        elif action == 'delete':
            contract.delete()
            messages.success(request, 'Contract deleted.')
            return redirect('contracts:contract_list', slug=slug)
        return redirect('contracts:contract_detail', slug=slug, pk=pk)
    return render(request, 'contracts/contract_detail.html', {
        'biz': biz, 'contract': contract, 'parties': parties,
    })


@login_required(login_url='/accounts/login/')
def templates(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            ContractTemplate.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                category=request.POST.get('category', '').strip(),
                content=request.POST.get('content', ''),
                created_by=request.user,
            )
            messages.success(request, 'Template created.')
        elif action == 'delete':
            ContractTemplate.objects.filter(pk=request.POST.get('template_id'), business=biz).delete()
            messages.success(request, 'Template deleted.')
        return redirect('contracts:templates', slug=slug)
    all_templates = ContractTemplate.objects.filter(business=biz).order_by('name')
    return render(request, 'contracts/templates.html', {'biz': biz, 'templates': all_templates})
