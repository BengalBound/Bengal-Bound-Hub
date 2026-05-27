from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import Department, JobPosition, Employee, LeaveType, LeaveRequest, PerformanceReview


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    stats = {
        'total': Employee.objects.filter(business=biz, status='active').count(),
        'on_leave': Employee.objects.filter(business=biz, status='on_leave').count(),
        'departments': Department.objects.filter(business=biz, is_active=True).count(),
        'pending_leaves': LeaveRequest.objects.filter(business=biz, status='pending').count(),
    }
    recent_employees = Employee.objects.filter(business=biz).order_by('-created_at')[:5]
    pending_leaves = LeaveRequest.objects.filter(business=biz, status='pending').select_related('employee', 'leave_type')[:10]
    return render(request, 'hr/index.html', {'biz': biz, 'stats': stats, 'recent_employees': recent_employees, 'pending_leaves': pending_leaves})


@login_required(login_url='/accounts/login/')
def employees(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    q = request.GET.get('q', '')
    dept = request.GET.get('dept', '')
    status = request.GET.get('status', '')
    qs = Employee.objects.filter(business=biz).select_related('department', 'position')
    if q:
        qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
    if dept:
        qs = qs.filter(department_id=dept)
    if status:
        qs = qs.filter(status=status)
    departments = Department.objects.filter(business=biz, is_active=True)
    return render(request, 'hr/employees.html', {'biz': biz, 'employees': qs, 'departments': departments, 'q': q, 'dept': dept, 'status_filter': status})


@login_required(login_url='/accounts/login/')
def employee_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    departments = Department.objects.filter(business=biz, is_active=True)
    positions = JobPosition.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        emp = Employee.objects.create(
            business=biz,
            first_name=request.POST.get('first_name', '').strip(),
            last_name=request.POST.get('last_name', '').strip(),
            email=request.POST.get('email', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            employee_id=request.POST.get('employee_id', '').strip(),
            gender=request.POST.get('gender', ''),
            contract_type=request.POST.get('contract_type', 'full_time'),
            hire_date=request.POST.get('hire_date') or timezone.now().date(),
            department_id=request.POST.get('department') or None,
            position_id=request.POST.get('position') or None,
            salary=request.POST.get('salary') or 0,
            work_location=request.POST.get('work_location', '').strip(),
        )
        messages.success(request, f'{emp.full_name} added.')
        return redirect('hr:employee_detail', slug=slug, pk=emp.pk)
    return render(request, 'hr/employee_form.html', {'biz': biz, 'departments': departments, 'positions': positions, 'employee': None})


@login_required(login_url='/accounts/login/')
def employee_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    emp = get_object_or_404(Employee, pk=pk, business=biz)
    departments = Department.objects.filter(business=biz, is_active=True)
    positions = JobPosition.objects.filter(business=biz, is_active=True)
    leave_requests = emp.leave_requests.order_by('-created_at')[:10]
    reviews = emp.reviews.order_by('-created_at')[:5]
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            for f in ['first_name', 'last_name', 'email', 'phone', 'work_location', 'bank_name', 'bank_account', 'address', 'emergency_contact_name', 'emergency_contact_phone', 'notes']:
                setattr(emp, f, request.POST.get(f, getattr(emp, f)))
            emp.salary = request.POST.get('salary', emp.salary)
            emp.department_id = request.POST.get('department') or emp.department_id
            emp.position_id = request.POST.get('position') or emp.position_id
            emp.status = request.POST.get('status', emp.status)
            emp.save()
            messages.success(request, 'Employee updated.')
        elif action == 'terminate':
            emp.status = 'terminated'
            emp.termination_date = request.POST.get('termination_date') or timezone.now().date()
            emp.save(update_fields=['status', 'termination_date'])
            messages.warning(request, f'{emp.full_name} terminated.')
        elif action == 'delete':
            emp.delete()
            messages.success(request, 'Employee deleted.')
            return redirect('hr:employees', slug=slug)
        return redirect('hr:employee_detail', slug=slug, pk=pk)
    return render(request, 'hr/employee_detail.html', {'biz': biz, 'emp': emp, 'departments': departments, 'positions': positions, 'leave_requests': leave_requests, 'reviews': reviews})


@login_required(login_url='/accounts/login/')
def departments(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Department.objects.create(business=biz, name=request.POST.get('name', '').strip(), code=request.POST.get('code', ''), description=request.POST.get('description', ''))
            messages.success(request, 'Department created.')
        elif action == 'delete':
            Department.objects.filter(pk=request.POST.get('dept_id'), business=biz).delete()
            messages.success(request, 'Department removed.')
        return redirect('hr:departments', slug=slug)
    depts = Department.objects.filter(business=biz).annotate(emp_count=Count('employees'))
    return render(request, 'hr/departments.html', {'biz': biz, 'departments': depts})


@login_required(login_url='/accounts/login/')
def leave_management(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status = request.GET.get('status', '')
    qs = LeaveRequest.objects.filter(business=biz).select_related('employee', 'leave_type')
    if status:
        qs = qs.filter(status=status)
    leave_types = LeaveType.objects.filter(business=biz)
    employees_qs = Employee.objects.filter(business=biz, status__in=['active', 'on_leave'])
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            emp = get_object_or_404(Employee, pk=request.POST.get('employee'), business=biz)
            lt = get_object_or_404(LeaveType, pk=request.POST.get('leave_type'), business=biz)
            LeaveRequest.objects.create(
                business=biz, employee=emp, leave_type=lt,
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
                days=int(request.POST.get('days', 1)),
                reason=request.POST.get('reason', ''),
            )
            messages.success(request, 'Leave request submitted.')
        elif action == 'create_type':
            LeaveType.objects.create(business=biz, name=request.POST.get('name', ''), days_allowed=int(request.POST.get('days_allowed', 0)), is_paid='is_paid' in request.POST)
            messages.success(request, 'Leave type added.')
        elif action in ('approve', 'reject'):
            lr = get_object_or_404(LeaveRequest, pk=request.POST.get('leave_id'), business=biz)
            lr.status = 'approved' if action == 'approve' else 'rejected'
            lr.reviewed_by = request.user
            lr.review_notes = request.POST.get('review_notes', '')
            lr.save(update_fields=['status', 'reviewed_by', 'review_notes'])
            messages.success(request, f'Leave {lr.status}.')
        return redirect('hr:leave_management', slug=slug)
    return render(request, 'hr/leave_management.html', {'biz': biz, 'leaves': qs, 'leave_types': leave_types, 'employees': employees_qs, 'status_filter': status})


@login_required(login_url='/accounts/login/')
def performance(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    reviews = PerformanceReview.objects.filter(business=biz).select_related('employee', 'reviewer')
    employees_qs = Employee.objects.filter(business=biz, status='active')
    if request.method == 'POST':
        emp = get_object_or_404(Employee, pk=request.POST.get('employee'), business=biz)
        PerformanceReview.objects.create(
            business=biz, employee=emp, reviewer=request.user,
            period_start=request.POST.get('period_start'),
            period_end=request.POST.get('period_end'),
            rating=request.POST.get('rating', ''),
            goals_achieved=request.POST.get('goals_achieved', ''),
            strengths=request.POST.get('strengths', ''),
            areas_to_improve=request.POST.get('areas_to_improve', ''),
            overall_comments=request.POST.get('overall_comments', ''),
        )
        messages.success(request, 'Performance review created.')
        return redirect('hr:performance', slug=slug)
    return render(request, 'hr/performance.html', {'biz': biz, 'reviews': reviews, 'employees': employees_qs})
