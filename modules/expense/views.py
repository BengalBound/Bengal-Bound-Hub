from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Sum

from hub.views import _get_business_for_user
from .models import ExpenseClaim, ExpenseItem, ExpenseCategory


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    claims = ExpenseClaim.objects.filter(business=biz)
    stats = {
        'total': claims.count(),
        'pending': claims.filter(status__in=['draft', 'submitted']).count(),
        'approved': claims.filter(status='approved').count(),
        'total_value': claims.filter(status='approved').aggregate(s=Sum('total_amount'))['s'] or 0,
    }
    recent = claims.order_by('-created_at')[:10]
    return render(request, 'expense/index.html', {'biz': biz, 'stats': stats, 'recent_claims': recent})


@login_required(login_url='/accounts/login/')
def claims(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status = request.GET.get('status', '')
    qs = ExpenseClaim.objects.filter(business=biz).select_related('submitted_by')
    if status:
        qs = qs.filter(status=status)
    categories = ExpenseCategory.objects.filter(business=biz)
    return render(request, 'expense/claims.html', {'biz': biz, 'claims': qs, 'status_filter': status, 'categories': categories})


@login_required(login_url='/accounts/login/')
def claim_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    categories = ExpenseCategory.objects.filter(business=biz)
    if request.method == 'POST':
        claim = ExpenseClaim.objects.create(
            business=biz, submitted_by=request.user,
            title=request.POST.get('title', '').strip(),
            description=request.POST.get('description', ''),
        )
        descs = request.POST.getlist('item_desc')
        amounts = request.POST.getlist('item_amount')
        dates = request.POST.getlist('item_date')
        cats = request.POST.getlist('item_cat')
        for i, desc in enumerate(descs):
            if desc.strip():
                ExpenseItem.objects.create(
                    claim=claim, description=desc.strip(),
                    amount=amounts[i] if i < len(amounts) else 0,
                    expense_date=dates[i] if i < len(dates) else None,
                    category_id=cats[i] if i < len(cats) and cats[i] else None,
                )
        claim.recalculate_total()
        if 'submit' in request.POST:
            claim.status = 'submitted'
            claim.save(update_fields=['status'])
        messages.success(request, f'Expense claim "{claim.title}" created.')
        return redirect('expense:claim_detail', slug=slug, pk=claim.pk)
    return render(request, 'expense/claim_form.html', {'biz': biz, 'categories': categories})


@login_required(login_url='/accounts/login/')
def claim_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    claim = get_object_or_404(ExpenseClaim, pk=pk, business=biz)
    items = claim.items.select_related('category')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'submit' and claim.status == 'draft':
            claim.status = 'submitted'
            claim.save(update_fields=['status'])
            messages.success(request, 'Claim submitted for approval.')
        elif action == 'approve':
            claim.status = 'approved'
            claim.reviewed_by = request.user
            claim.save(update_fields=['status', 'reviewed_by'])
            messages.success(request, 'Claim approved.')
        elif action == 'reject':
            claim.status = 'rejected'
            claim.reviewed_by = request.user
            claim.review_notes = request.POST.get('notes', '')
            claim.save(update_fields=['status', 'reviewed_by', 'review_notes'])
            messages.info(request, 'Claim rejected.')
        elif action == 'delete':
            claim.delete()
            messages.success(request, 'Claim deleted.')
            return redirect('expense:claims', slug=slug)
        return redirect('expense:claim_detail', slug=slug, pk=pk)
    return render(request, 'expense/claim_detail.html', {'biz': biz, 'claim': claim, 'items': items})
