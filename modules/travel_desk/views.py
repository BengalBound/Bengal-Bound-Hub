from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from hub.models import BusinessInstance, BusinessEmployee
from .models import CorporateAccount, TravelPolicy, TravelRequest, TravelExpense


def _check(slug, user, min_level=1):
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
def td_home(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    all_requests = TravelRequest.objects.filter(business=biz)
    completed = all_requests.filter(status='completed')
    total_spend = sum(r.actual_cost for r in completed)

    stats = {
        'total_requests': all_requests.count(),
        'pending_requests': all_requests.filter(status='pending').count(),
        'approved': all_requests.filter(status='approved').count(),
        'total_spend': total_spend,
    }

    corporate_accounts = CorporateAccount.objects.filter(business=biz, is_active=True)

    return render(request, 'travel_desk/home.html', {
        'biz': biz,
        'access_level': level,
        'stats': stats,
        'corporate_accounts': corporate_accounts,
    })


@login_required
def accounts(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_account':
            CorporateAccount.objects.create(
                business=biz,
                company_name=request.POST.get('company_name', ''),
                contact_name=request.POST.get('contact_name', ''),
                contact_email=request.POST.get('contact_email', ''),
                contact_phone=request.POST.get('contact_phone', ''),
                credit_limit=request.POST.get('credit_limit', 0),
                currency=request.POST.get('currency', 'USD'),
                travel_policy_url=request.POST.get('travel_policy_url', ''),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Corporate account added.')
        elif action == 'toggle_account':
            account = get_object_or_404(CorporateAccount, pk=request.POST.get('account_id'), business=biz)
            account.is_active = not account.is_active
            account.save(update_fields=['is_active'])
            messages.success(request, 'Account status updated.')
        return redirect('travel_desk:accounts', slug=slug)

    corporate_accounts = CorporateAccount.objects.filter(business=biz)

    return render(request, 'travel_desk/accounts.html', {
        'biz': biz,
        'access_level': level,
        'corporate_accounts': corporate_accounts,
    })


@login_required
def policy(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_policy':
            TravelPolicy.objects.create(
                business=biz,
                name=request.POST.get('name', ''),
                applies_to=request.POST.get('applies_to', 'all'),
                max_hotel_rate_usd=request.POST.get('max_hotel_rate_usd') or None,
                max_flight_economy=request.POST.get('max_flight_economy') == 'on',
                require_advance_booking_days=request.POST.get('require_advance_booking_days', 7),
                require_approval=request.POST.get('require_approval') == 'on',
                approval_threshold=request.POST.get('approval_threshold', 500),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Travel policy added.')
        return redirect('travel_desk:policy', slug=slug)

    policies = TravelPolicy.objects.filter(business=biz)

    return render(request, 'travel_desk/policy.html', {
        'biz': biz,
        'access_level': level,
        'policies': policies,
    })


@login_required
def requests(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_request' and level >= 2:
            corporate_account_id = request.POST.get('corporate_account_id')
            corporate_account = (
                CorporateAccount.objects.filter(pk=corporate_account_id, business=biz).first()
                if corporate_account_id else None
            )
            tr = TravelRequest.objects.create(
                business=biz,
                requester=emp,
                corporate_account=corporate_account,
                trip_purpose=request.POST.get('trip_purpose', ''),
                departure_date=request.POST.get('departure_date', ''),
                return_date=request.POST.get('return_date') or None,
                origin=request.POST.get('origin', ''),
                destination=request.POST.get('destination', ''),
                travel_type=request.POST.get('travel_type', 'flight_hotel'),
                estimated_cost=request.POST.get('estimated_cost', 0),
                currency=request.POST.get('currency', 'USD'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, f'Travel request {tr.request_number} created.')

        elif action == 'approve_request' and level >= 3:
            tr = get_object_or_404(TravelRequest, pk=request.POST.get('request_id'), business=biz)
            tr.status = 'approved'
            tr.approved_by = emp
            tr.approved_at = timezone.now()
            tr.save(update_fields=['status', 'approved_by', 'approved_at'])
            messages.success(request, f'Request {tr.request_number} approved.')

        elif action == 'reject_request' and level >= 3:
            tr = get_object_or_404(TravelRequest, pk=request.POST.get('request_id'), business=biz)
            tr.status = 'rejected'
            tr.rejection_reason = request.POST.get('rejection_reason', '')
            tr.save(update_fields=['status', 'rejection_reason'])
            messages.success(request, f'Request {tr.request_number} rejected.')

        elif action == 'mark_booked' and level >= 3:
            tr = get_object_or_404(TravelRequest, pk=request.POST.get('request_id'), business=biz)
            tr.status = 'booked'
            tr.booking_reference = request.POST.get('booking_reference', '')
            tr.save(update_fields=['status', 'booking_reference'])
            messages.success(request, f'Request {tr.request_number} marked as booked.')

        return redirect('travel_desk:requests', slug=slug)

    travel_requests = TravelRequest.objects.filter(business=biz).select_related(
        'requester__user', 'approved_by__user', 'corporate_account'
    )
    status_filter = request.GET.get('status', '')
    if status_filter:
        travel_requests = travel_requests.filter(status=status_filter)

    corporate_accounts = CorporateAccount.objects.filter(business=biz, is_active=True)

    return render(request, 'travel_desk/requests.html', {
        'biz': biz,
        'access_level': level,
        'travel_requests': travel_requests,
        'status_filter': status_filter,
        'corporate_accounts': corporate_accounts,
    })


@login_required
def request_detail(request, slug, req_id):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    tr = get_object_or_404(TravelRequest, pk=req_id, business=biz)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_expense' and level >= 2:
            TravelExpense.objects.create(
                travel_request=tr,
                expense_type=request.POST.get('expense_type', ''),
                description=request.POST.get('description', ''),
                amount=request.POST.get('amount', ''),
                currency=request.POST.get('currency', 'USD'),
                receipt_url=request.POST.get('receipt_url', ''),
            )
            messages.success(request, 'Expense added.')

        elif action == 'approve_expense' and level >= 3:
            expense = get_object_or_404(TravelExpense, pk=request.POST.get('expense_id'), travel_request=tr)
            expense.is_approved = True
            expense.save(update_fields=['is_approved'])
            messages.success(request, 'Expense approved.')

        return redirect('travel_desk:request_detail', slug=slug, req_id=req_id)

    expenses = tr.expenses.all()

    return render(request, 'travel_desk/request_detail.html', {
        'biz': biz,
        'access_level': level,
        'tr': tr,
        'expenses': expenses,
    })
