from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q

from hub.views import _get_business_for_user
from hub.access import get_member_context, require_employee, require_manager, require_audit_manager

from .models import OperationalReport, UserExpense

try:
    from modules.invoicing.models import Invoice, Payment
except ImportError:
    Invoice = Payment = None

try:
    from modules.expense.models import ExpenseClaim
except ImportError:
    ExpenseClaim = None

try:
    from modules.payroll.models import Payslip
except ImportError:
    Payslip = None


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if not biz:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    member, level, is_owner = get_member_context(biz, request.user)

    my_reports = OperationalReport.objects.filter(business=biz, submitted_by=request.user).count()
    my_expenses = UserExpense.objects.filter(business=biz, submitted_by=request.user).count()
    pending_reports = OperationalReport.objects.filter(business=biz, status='submitted').count() if level >= 6 else 0
    pending_expenses = UserExpense.objects.filter(business=biz, status='submitted').count() if level >= 6 else 0

    return render(request, 'financials/index.html', {
        'biz': biz,
        'member': member,
        'access_level': level,
        'is_owner': is_owner,
        'my_reports': my_reports,
        'my_expenses': my_expenses,
        'pending_reports': pending_reports,
        'pending_expenses': pending_expenses,
        'current_business': biz,
    })


@require_audit_manager
def financial_dashboard(request, slug):
    biz = _get_business_for_user(slug, request.user)
    member, level, is_owner = get_member_context(biz, request.user)

    # --- Revenue (invoicing module) ---
    total_revenue = 0
    total_invoiced = 0
    outstanding = 0
    invoice_count = 0
    if Invoice:
        qs = Invoice.objects.filter(business=biz)
        total_invoiced = qs.aggregate(s=Sum('total'))['s'] or 0
        paid_qs = qs.filter(status__in=['paid', 'partial'])
        total_revenue = paid_qs.aggregate(s=Sum('amount_paid'))['s'] or 0
        outstanding = total_invoiced - total_revenue
        invoice_count = qs.count()

    # --- Operating Expenses (expense module claims) ---
    claimed_expense_total = 0
    if ExpenseClaim:
        claimed_expense_total = ExpenseClaim.objects.filter(
            business=biz, status='approved'
        ).aggregate(s=Sum('total_amount'))['s'] or 0

    # --- Staff Expenses (this module's UserExpense) ---
    staff_expense_total = UserExpense.objects.filter(
        business=biz, status='approved'
    ).aggregate(s=Sum('amount'))['s'] or 0

    # Category breakdown of staff expenses
    expense_by_category = (
        UserExpense.objects
        .filter(business=biz, status='approved')
        .values('category_name')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )

    # --- Payroll ---
    payroll_total = 0
    if Payslip:
        payroll_total = Payslip.objects.filter(
            pay_period__business=biz, status='paid'
        ).aggregate(s=Sum('net_pay'))['s'] or 0

    total_expenses = claimed_expense_total + staff_expense_total + payroll_total
    net_profit = total_revenue - total_expenses

    # Recent submitted reports awaiting approval
    pending_reports = OperationalReport.objects.filter(business=biz, status='submitted').order_by('-created_at')[:10]

    # Recent approved expenses
    recent_expenses = UserExpense.objects.filter(business=biz).order_by('-created_at')[:10]

    return render(request, 'financials/financial_dashboard.html', {
        'biz': biz,
        'member': member,
        'access_level': level,
        'is_owner': is_owner,
        'total_revenue': total_revenue,
        'total_invoiced': total_invoiced,
        'outstanding': outstanding,
        'invoice_count': invoice_count,
        'claimed_expense_total': claimed_expense_total,
        'staff_expense_total': staff_expense_total,
        'payroll_total': payroll_total,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'expense_by_category': expense_by_category,
        'pending_reports': pending_reports,
        'recent_expenses': recent_expenses,
        'current_business': biz,
    })


@require_employee
def report_list(request, slug):
    biz = _get_business_for_user(slug, request.user)
    member, level, is_owner = get_member_context(biz, request.user)

    if level >= 6:
        # Managers and above see all submitted/approved/rejected reports
        reports = OperationalReport.objects.filter(business=biz)
    else:
        # Regular employees only see their own
        reports = OperationalReport.objects.filter(business=biz, submitted_by=request.user)

    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    if status_filter:
        reports = reports.filter(status=status_filter)
    if type_filter:
        reports = reports.filter(report_type=type_filter)

    return render(request, 'financials/report_list.html', {
        'biz': biz,
        'reports': reports,
        'access_level': level,
        'is_owner': is_owner,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'report_types': OperationalReport.TYPES,
        'current_business': biz,
    })


@require_employee
def report_submit(request, slug):
    biz = _get_business_for_user(slug, request.user)
    member, level, is_owner = get_member_context(biz, request.user)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        report_type = request.POST.get('report_type', 'daily_ops')
        period_start = request.POST.get('period_start')
        period_end = request.POST.get('period_end')
        content = request.POST.get('content', '').strip()
        summary = request.POST.get('summary', '').strip()
        action = request.POST.get('action', 'draft')

        if not title or not content or not period_start or not period_end:
            messages.error(request, 'Title, period, and content are required.')
        else:
            status = 'submitted' if action == 'submit' else 'draft'
            OperationalReport.objects.create(
                business=biz,
                submitted_by=request.user,
                report_type=report_type,
                title=title,
                period_start=period_start,
                period_end=period_end,
                content=content,
                summary=summary,
                status=status,
            )
            msg = 'Report submitted for review.' if status == 'submitted' else 'Report saved as draft.'
            messages.success(request, msg)
            return redirect('financials:report_list', slug=slug)

    return render(request, 'financials/report_submit.html', {
        'biz': biz,
        'access_level': level,
        'report_types': OperationalReport.TYPES,
        'today': timezone.now().date(),
        'current_business': biz,
    })


@require_employee
def report_detail(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    member, level, is_owner = get_member_context(biz, request.user)
    report = get_object_or_404(OperationalReport, pk=pk, business=biz)

    # Non-managers can only view their own
    if level < 6 and report.submitted_by != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    if request.method == 'POST' and level >= 6:
        action = request.POST.get('action')
        notes = request.POST.get('review_notes', '').strip()
        if action == 'approve' and report.status == 'submitted':
            report.status = 'approved'
            report.reviewed_by = request.user
            report.review_date = timezone.now()
            report.review_notes = notes
            report.save()
            messages.success(request, 'Report approved.')
        elif action == 'reject' and report.status == 'submitted':
            if not notes:
                messages.error(request, 'Please provide rejection notes.')
            else:
                report.status = 'rejected'
                report.reviewed_by = request.user
                report.review_date = timezone.now()
                report.review_notes = notes
                report.save()
                messages.warning(request, 'Report rejected.')
        elif action == 'submit' and report.submitted_by == request.user and report.status == 'draft':
            report.status = 'submitted'
            report.save()
            messages.success(request, 'Report submitted for review.')
        return redirect('financials:report_detail', slug=slug, pk=pk)

    return render(request, 'financials/report_detail.html', {
        'biz': biz,
        'report': report,
        'access_level': level,
        'is_owner': is_owner,
        'current_business': biz,
    })


@require_employee
def log_expense(request, slug):
    biz = _get_business_for_user(slug, request.user)
    member, level, is_owner = get_member_context(biz, request.user)

    # Suggest categories from existing ones for this business
    existing_categories = (
        UserExpense.objects
        .filter(business=biz)
        .values_list('category_name', flat=True)
        .distinct()
        .order_by('category_name')
    )

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        amount = request.POST.get('amount', '').strip()
        category_name = request.POST.get('category_name', '').strip()
        department = request.POST.get('department', '').strip()
        expense_date = request.POST.get('expense_date') or timezone.now().date()
        description = request.POST.get('description', '').strip()
        action = request.POST.get('action', 'draft')
        receipt = request.FILES.get('receipt')

        if not title or not amount or not category_name:
            messages.error(request, 'Title, amount, and category are required.')
        else:
            try:
                amount_val = float(amount)
                status = 'submitted' if action == 'submit' else 'draft'
                expense = UserExpense.objects.create(
                    business=biz,
                    submitted_by=request.user,
                    title=title,
                    amount=amount_val,
                    category_name=category_name,
                    department=department,
                    expense_date=expense_date,
                    description=description,
                    status=status,
                )
                if receipt:
                    expense.receipt = receipt
                    expense.save(update_fields=['receipt'])
                msg = 'Expense submitted for approval.' if status == 'submitted' else 'Expense saved as draft.'
                messages.success(request, msg)
                return redirect('financials:my_expenses', slug=slug)
            except ValueError:
                messages.error(request, 'Invalid amount.')

    return render(request, 'financials/expense_log.html', {
        'biz': biz,
        'access_level': level,
        'existing_categories': existing_categories,
        'today': timezone.now().date(),
        'current_business': biz,
    })


@require_employee
def my_expenses(request, slug):
    biz = _get_business_for_user(slug, request.user)
    member, level, is_owner = get_member_context(biz, request.user)

    expenses = UserExpense.objects.filter(business=biz, submitted_by=request.user)

    status_filter = request.GET.get('status', '')
    if status_filter:
        expenses = expenses.filter(status=status_filter)

    total_approved = expenses.filter(status='approved').aggregate(s=Sum('amount'))['s'] or 0
    total_pending = expenses.filter(status='submitted').aggregate(s=Sum('amount'))['s'] or 0

    return render(request, 'financials/my_expenses.html', {
        'biz': biz,
        'expenses': expenses,
        'access_level': level,
        'status_filter': status_filter,
        'total_approved': total_approved,
        'total_pending': total_pending,
        'current_business': biz,
    })


@require_manager
def expense_overview(request, slug):
    biz = _get_business_for_user(slug, request.user)
    member, level, is_owner = get_member_context(biz, request.user)

    # Approval queue
    pending = UserExpense.objects.filter(business=biz, status='submitted').order_by('-created_at')

    if request.method == 'POST':
        expense_id = request.POST.get('expense_id')
        action = request.POST.get('action')
        notes = request.POST.get('approval_notes', '').strip()
        expense = get_object_or_404(UserExpense, pk=expense_id, business=biz)

        if action == 'approve':
            expense.status = 'approved'
            expense.approved_by = request.user
            expense.approval_date = timezone.now()
            expense.approval_notes = notes
            expense.save()
            messages.success(request, f'Expense "{expense.title}" approved.')
        elif action == 'reject':
            if not notes:
                messages.error(request, 'Please provide rejection notes.')
            else:
                expense.status = 'rejected'
                expense.approved_by = request.user
                expense.approval_date = timezone.now()
                expense.approval_notes = notes
                expense.save()
                messages.warning(request, f'Expense "{expense.title}" rejected.')
        return redirect('financials:expense_overview', slug=slug)

    # Summary by category (approved)
    by_category = (
        UserExpense.objects
        .filter(business=biz, status='approved')
        .values('category_name')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )

    # Summary by department (approved)
    by_dept = (
        UserExpense.objects
        .filter(business=biz, status='approved')
        .exclude(department='')
        .values('department')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )

    grand_total_approved = UserExpense.objects.filter(business=biz, status='approved').aggregate(s=Sum('amount'))['s'] or 0

    all_expenses = UserExpense.objects.filter(business=biz).order_by('-created_at')[:50]

    return render(request, 'financials/expense_overview.html', {
        'biz': biz,
        'member': member,
        'access_level': level,
        'is_owner': is_owner,
        'pending': pending,
        'by_category': by_category,
        'by_dept': by_dept,
        'grand_total_approved': grand_total_approved,
        'all_expenses': all_expenses,
        'current_business': biz,
    })
