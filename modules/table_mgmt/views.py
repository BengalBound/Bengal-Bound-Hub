from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import DiningArea, Table, Reservation


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    today = timezone.now().date()
    stats = {
        'total_tables': Table.objects.filter(business=biz, is_active=True).count(),
        'available': Table.objects.filter(business=biz, status='available', is_active=True).count(),
        'occupied': Table.objects.filter(business=biz, status='occupied', is_active=True).count(),
        'reservations_today': Reservation.objects.filter(business=biz, date=today).count(),
    }
    areas = DiningArea.objects.filter(business=biz, is_active=True).prefetch_related('tables')
    upcoming_reservations = Reservation.objects.filter(
        business=biz, date__gte=today, status__in=['pending', 'confirmed']
    ).order_by('date', 'time')[:10]
    return render(request, 'table_mgmt/index.html', {
        'biz': biz, 'stats': stats, 'areas': areas, 'upcoming_reservations': upcoming_reservations,
    })


@login_required(login_url='/accounts/login/')
def floor_plan(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    areas = DiningArea.objects.filter(business=biz, is_active=True)
    tables = Table.objects.filter(business=biz, is_active=True).select_related('area')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_area':
            DiningArea.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', ''),
            )
            messages.success(request, 'Dining area created.')
        elif action == 'create_table':
            Table.objects.create(
                business=biz,
                area_id=request.POST.get('area') or None,
                table_number=request.POST.get('table_number', '').strip(),
                capacity=request.POST.get('capacity', 4) or 4,
                shape=request.POST.get('shape', 'square'),
            )
            messages.success(request, 'Table created.')
        elif action == 'update_table_status':
            table = get_object_or_404(Table, pk=request.POST.get('table_id'), business=biz)
            table.status = request.POST.get('status', table.status)
            table.save(update_fields=['status'])
            messages.success(request, f'Table {table.table_number} status updated.')
        elif action == 'delete_table':
            Table.objects.filter(pk=request.POST.get('table_id'), business=biz).delete()
            messages.success(request, 'Table removed.')
        return redirect('table_mgmt:floor_plan', slug=slug)
    return render(request, 'table_mgmt/floor_plan.html', {
        'biz': biz, 'areas': areas, 'tables': tables,
    })


@login_required(login_url='/accounts/login/')
def reservations(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    date_filter = request.GET.get('date', '')
    status_filter = request.GET.get('status', '')
    qs = Reservation.objects.filter(business=biz).select_related('table', 'created_by').order_by('-date', '-time')
    if date_filter:
        qs = qs.filter(date=date_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)
    tables = Table.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Reservation.objects.create(
                business=biz,
                table_id=request.POST.get('table') or None,
                customer_name=request.POST.get('customer_name', '').strip(),
                customer_email=request.POST.get('customer_email', '').strip(),
                customer_phone=request.POST.get('customer_phone', '').strip(),
                party_size=request.POST.get('party_size', 2) or 2,
                date=request.POST.get('date'),
                time=request.POST.get('time'),
                duration_minutes=request.POST.get('duration_minutes', 90) or 90,
                special_requests=request.POST.get('special_requests', ''),
                occasion=request.POST.get('occasion', '').strip(),
                created_by=request.user,
            )
            messages.success(request, 'Reservation created.')
        elif action == 'update_status':
            res = get_object_or_404(Reservation, pk=request.POST.get('reservation_id'), business=biz)
            res.status = request.POST.get('status', res.status)
            res.save(update_fields=['status'])
            if res.table and res.status == 'seated':
                res.table.status = 'occupied'
                res.table.save(update_fields=['status'])
            messages.success(request, f'Reservation {res.get_status_display()}.')
        return redirect('table_mgmt:reservations', slug=slug)
    return render(request, 'table_mgmt/reservations.html', {
        'biz': biz, 'reservations': qs, 'tables': tables,
        'date_filter': date_filter, 'status_filter': status_filter,
    })
