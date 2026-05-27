from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages

from hub.views import _get_business_for_user
from .models import BudgetPeriod, Budget, BudgetLine


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    budgets = Budget.objects.filter(business=biz)
    active_qs = budgets.filter(status__in=['active', 'approved'])
    recent = budgets.select_related('period', 'created_by').order_by('-created_at')[:10]
    return render(request, 'budgeting/index.html', {
        'biz': biz,
        'total_budgets': budgets.count(),
        'active_budgets': budgets.filter(status='active').count(),
        'active_periods': BudgetPeriod.objects.filter(business=biz, is_active=True).count(),
        'total_budgeted': sum(b.total_budgeted for b in active_qs),
        'recent_budgets': recent,
    })


@login_required(login_url='/accounts/login/')
def periods(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            BudgetPeriod.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
            )
            messages.success(request, 'Budget period created.')
        elif action == 'delete':
            BudgetPeriod.objects.filter(pk=request.POST.get('period_id'), business=biz).delete()
            messages.success(request, 'Period deleted.')
        return redirect('budgeting:periods', slug=slug)
    all_periods = BudgetPeriod.objects.filter(business=biz).order_by('-start_date')
    return render(request, 'budgeting/periods.html', {'biz': biz, 'periods': all_periods})


@login_required(login_url='/accounts/login/')
def budget_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status_filter = request.GET.get('status', '')
    qs = Budget.objects.filter(business=biz).select_related('period', 'created_by', 'approved_by').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    periods_qs = BudgetPeriod.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Budget.objects.create(
                business=biz,
                period_id=request.POST.get('period'),
                name=request.POST.get('name', '').strip(),
                department=request.POST.get('department', '').strip(),
                currency=request.POST.get('currency', 'USD').strip(),
                notes=request.POST.get('notes', ''),
                created_by=request.user,
            )
            messages.success(request, 'Budget created.')
        return redirect('budgeting:budget_list', slug=slug)
    return render(request, 'budgeting/budget_list.html', {
        'biz': biz, 'budgets': qs, 'periods': periods_qs, 'status_filter': status_filter,
    })


@login_required(login_url='/accounts/login/')
def budget_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    budget = get_object_or_404(Budget, pk=pk, business=biz)
    lines = budget.lines.order_by('category', 'account_name')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_line':
            BudgetLine.objects.create(
                budget=budget,
                account_name=request.POST.get('account_name', '').strip(),
                category=request.POST.get('category', '').strip(),
                budgeted_amount=request.POST.get('budgeted_amount', 0) or 0,
                actual_amount=request.POST.get('actual_amount', 0) or 0,
                notes=request.POST.get('notes', ''),
            )
            budget.total_budgeted = sum(l.budgeted_amount for l in budget.lines.all())
            budget.total_actual = sum(l.actual_amount for l in budget.lines.all())
            budget.save(update_fields=['total_budgeted', 'total_actual'])
            messages.success(request, 'Budget line added.')
        elif action == 'update_line':
            line = get_object_or_404(BudgetLine, pk=request.POST.get('line_id'), budget=budget)
            line.actual_amount = request.POST.get('actual_amount', line.actual_amount) or line.actual_amount
            line.notes = request.POST.get('notes', line.notes)
            line.save(update_fields=['actual_amount', 'notes'])
            budget.total_actual = sum(l.actual_amount for l in budget.lines.all())
            budget.save(update_fields=['total_actual'])
            messages.success(request, 'Line updated.')
        elif action == 'approve':
            budget.status = 'approved'
            budget.approved_by = request.user
            budget.save(update_fields=['status', 'approved_by'])
            messages.success(request, 'Budget approved.')
        elif action == 'delete':
            budget.delete()
            messages.success(request, 'Budget deleted.')
            return redirect('budgeting:budget_list', slug=slug)
        return redirect('budgeting:budget_detail', slug=slug, pk=pk)
    return render(request, 'budgeting/budget_detail.html', {
        'biz': biz, 'budget': budget, 'lines': lines,
    })
