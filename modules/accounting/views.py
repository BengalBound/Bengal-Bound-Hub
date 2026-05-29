from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import Account, AccountCategory, JournalEntry, JournalLine, TaxRate


def _biz(slug, user):
    return _get_business_for_user(slug, user)


def _ensure_defaults(biz):
    if not Account.objects.filter(business=biz).exists():
        cat_asset, _ = AccountCategory.objects.get_or_create(business=biz, name='Assets', defaults={'account_type': 'asset'})
        cat_liab, _ = AccountCategory.objects.get_or_create(business=biz, name='Liabilities', defaults={'account_type': 'liability'})
        cat_inc, _ = AccountCategory.objects.get_or_create(business=biz, name='Income', defaults={'account_type': 'income'})
        cat_exp, _ = AccountCategory.objects.get_or_create(business=biz, name='Expenses', defaults={'account_type': 'expense'})
        defaults = [
            ('1000', 'Cash', 'asset', cat_asset), ('1100', 'Accounts Receivable', 'asset', cat_asset),
            ('2000', 'Accounts Payable', 'liability', cat_liab), ('3000', 'Revenue', 'income', cat_inc),
            ('4000', 'Operating Expenses', 'expense', cat_exp),
        ]
        for code, name, atype, cat in defaults:
            Account.objects.get_or_create(business=biz, code=code, defaults={'name': name, 'account_type': atype, 'category': cat})


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    _ensure_defaults(biz)
    accounts = Account.objects.filter(business=biz, is_active=True)
    entries = JournalEntry.objects.filter(business=biz).order_by('-date')[:10]
    income = accounts.filter(account_type='income')
    expenses = accounts.filter(account_type='expense')
    total_income = sum(a.get_balance() for a in income)
    total_expenses = sum(a.get_balance() for a in expenses)
    return render(request, 'accounting/index.html', {
        'biz': biz, 'accounts': accounts, 'recent_entries': entries,
        'total_income': total_income, 'total_expenses': total_expenses,
        'net_profit': total_income - total_expenses,
    })


@login_required(login_url='/accounts/login/')
def chart_of_accounts(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    _ensure_defaults(biz)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Account.objects.create(
                business=biz, code=request.POST.get('code', '').strip(),
                name=request.POST.get('name', '').strip(),
                account_type=request.POST.get('account_type', 'asset'),
                description=request.POST.get('description', ''),
            )
            messages.success(request, 'Account created.')
        elif action == 'delete':
            Account.objects.filter(pk=request.POST.get('account_id'), business=biz).delete()
            messages.success(request, 'Account deleted.')
        return redirect('accounting:chart_of_accounts', slug=slug)
    accounts = Account.objects.filter(business=biz).order_by('code')
    return render(request, 'accounting/chart_of_accounts.html', {'biz': biz, 'accounts': accounts})


@login_required(login_url='/accounts/login/')
def journal_entries(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    qs = JournalEntry.objects.filter(business=biz).order_by('-date')
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
    return render(request, 'accounting/journal_entries.html', {'biz': biz, 'entries': qs, 'status_filter': status})


@login_required(login_url='/accounts/login/')
def journal_entry_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    accounts = Account.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        entry = JournalEntry.objects.create(
            business=biz, date=request.POST.get('date', timezone.now().date()),
            description=request.POST.get('description', '').strip(),
            entry_type=request.POST.get('entry_type', 'general'),
            reference=request.POST.get('reference', '').strip(),
            created_by=request.user,
        )
        account_ids = request.POST.getlist('account_id')
        debits = request.POST.getlist('debit')
        credits = request.POST.getlist('credit')
        descs = request.POST.getlist('line_desc')
        for i, acc_id in enumerate(account_ids):
            if acc_id:
                JournalLine.objects.create(
                    entry=entry,
                    account_id=acc_id,
                    debit=debits[i] if i < len(debits) else 0,
                    credit=credits[i] if i < len(credits) else 0,
                    description=descs[i] if i < len(descs) else '',
                )
        if entry.is_balanced():
            entry.status = 'posted'
            entry.save(update_fields=['status'])
        messages.success(request, f'Journal entry created ({"posted" if entry.is_balanced() else "draft — not balanced"}).')
        return redirect('accounting:journal_entries', slug=slug)
    return render(request, 'accounting/journal_entry_form.html', {'biz': biz, 'accounts': accounts})


@login_required(login_url='/accounts/login/')
def tax_rates(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            TaxRate.objects.create(business=biz, name=request.POST.get('name', '').strip(), rate=request.POST.get('rate', 0))
            messages.success(request, 'Tax rate added.')
        elif action == 'delete':
            TaxRate.objects.filter(pk=request.POST.get('rate_id'), business=biz).delete()
            messages.success(request, 'Tax rate deleted.')
        return redirect('accounting:tax_rates', slug=slug)
    rates = TaxRate.objects.filter(business=biz)
    return render(request, 'accounting/tax_rates.html', {'biz': biz, 'rates': rates})
