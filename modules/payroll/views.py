from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Sum

from hub.views import _get_business_for_user
from .models import SalaryStructure, SalaryComponent, PayPeriod, Payslip

try:
    from modules.hr.models import Employee
except ImportError:
    Employee = None


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    periods = PayPeriod.objects.filter(business=biz).order_by('-start_date')[:5]
    stats = {
        'total_employees': Employee.objects.filter(business=biz, status='active').count() if Employee else 0,
        'pay_periods': PayPeriod.objects.filter(business=biz).count(),
        'total_paid': PayPeriod.objects.filter(business=biz, status='paid').aggregate(s=Sum('payslips__net_pay'))['s'] or 0,
        'pending_payroll': PayPeriod.objects.filter(business=biz, status__in=['draft', 'processing']).count(),
    }
    return render(request, 'payroll/index.html', {'biz': biz, 'stats': stats, 'recent_periods': periods})


@login_required(login_url='/accounts/login/')
def pay_periods(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            PayPeriod.objects.create(
                business=biz, name=request.POST.get('name', '').strip(),
                frequency=request.POST.get('frequency', 'monthly'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
                payment_date=request.POST.get('payment_date') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Pay period created.')
        return redirect('payroll:pay_periods', slug=slug)
    periods = PayPeriod.objects.filter(business=biz).order_by('-start_date')
    return render(request, 'payroll/pay_periods.html', {'biz': biz, 'periods': periods})


@login_required(login_url='/accounts/login/')
def payslips(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    period_id = request.GET.get('period', '')
    qs = Payslip.objects.filter(pay_period__business=biz).select_related('employee', 'pay_period')
    if period_id:
        qs = qs.filter(pay_period_id=period_id)
    periods = PayPeriod.objects.filter(business=biz).order_by('-start_date')
    return render(request, 'payroll/payslips.html', {'biz': biz, 'payslips': qs, 'periods': periods, 'period_id': period_id})


@login_required(login_url='/accounts/login/')
def structures(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            SalaryStructure.objects.create(business=biz, name=request.POST.get('name', '').strip(), description=request.POST.get('description', ''))
            messages.success(request, 'Salary structure created.')
        elif action == 'add_component':
            struct = get_object_or_404(SalaryStructure, pk=request.POST.get('struct_id'), business=biz)
            SalaryComponent.objects.create(
                structure=struct, name=request.POST.get('comp_name', ''),
                component_type=request.POST.get('comp_type', 'earning'),
                calculation_type=request.POST.get('calc_type', 'fixed'),
                amount=request.POST.get('amount') or 0,
            )
            messages.success(request, 'Component added.')
        return redirect('payroll:structures', slug=slug)
    all_structures = SalaryStructure.objects.filter(business=biz).prefetch_related('components')
    return render(request, 'payroll/structures.html', {'biz': biz, 'structures': all_structures})
