from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import AttendanceRecord, Timesheet

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
    today = timezone.now().date()
    stats = {
        'present_today': AttendanceRecord.objects.filter(business=biz, date=today, status='present').count(),
        'absent_today': AttendanceRecord.objects.filter(business=biz, date=today, status='absent').count(),
        'on_leave': AttendanceRecord.objects.filter(business=biz, date=today, status='leave').count(),
        'pending_timesheets': Timesheet.objects.filter(business=biz, status='submitted').count(),
    }
    recent_records = AttendanceRecord.objects.filter(business=biz).select_related('employee').order_by('-date')[:20]
    return render(request, 'attendance/index.html', {'biz': biz, 'stats': stats, 'recent_records': recent_records, 'today': today})


@login_required(login_url='/accounts/login/')
def attendance_records(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    date_filter = request.GET.get('date', '')
    qs = AttendanceRecord.objects.filter(business=biz).select_related('employee').order_by('-date')
    if date_filter:
        qs = qs.filter(date=date_filter)
    employees = Employee.objects.filter(business=biz, status='active') if Employee else []
    if request.method == 'POST':
        emp = get_object_or_404(Employee, pk=request.POST.get('employee'), business=biz)
        rec, created = AttendanceRecord.objects.get_or_create(
            business=biz, employee=emp, date=request.POST.get('date', timezone.now().date()),
            defaults={'status': request.POST.get('status', 'present'), 'check_in': request.POST.get('check_in') or None, 'check_out': request.POST.get('check_out') or None}
        )
        if not created:
            rec.status = request.POST.get('status', rec.status)
            rec.check_in = request.POST.get('check_in') or rec.check_in
            rec.check_out = request.POST.get('check_out') or rec.check_out
            rec.save()
        messages.success(request, 'Attendance recorded.')
        return redirect('attendance:attendance_records', slug=slug)
    return render(request, 'attendance/attendance_records.html', {'biz': biz, 'records': qs, 'employees': employees, 'date_filter': date_filter})


@login_required(login_url='/accounts/login/')
def timesheets(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status = request.GET.get('status', '')
    qs = Timesheet.objects.filter(business=biz).select_related('employee', 'approved_by').order_by('-week_start')
    if status:
        qs = qs.filter(status=status)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ('approve', 'reject'):
            ts = get_object_or_404(Timesheet, pk=request.POST.get('ts_id'), business=biz)
            ts.status = 'approved' if action == 'approve' else 'rejected'
            ts.approved_by = request.user
            ts.save(update_fields=['status', 'approved_by'])
            messages.success(request, f'Timesheet {ts.status}.')
        return redirect('attendance:timesheets', slug=slug)
    return render(request, 'attendance/timesheets.html', {'biz': biz, 'timesheets': qs, 'status_filter': status})
