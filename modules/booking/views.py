from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import BookingService, Booking


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    today = timezone.now().date()
    stats = {
        'services': BookingService.objects.filter(business=biz, is_active=True).count(),
        'today': Booking.objects.filter(business=biz, date=today).count(),
        'pending': Booking.objects.filter(business=biz, status='pending').count(),
        'confirmed': Booking.objects.filter(business=biz, status='confirmed', date__gte=today).count(),
    }
    upcoming = Booking.objects.filter(business=biz, date__gte=today).select_related('service', 'staff').order_by('date', 'start_time')[:15]
    return render(request, 'booking/index.html', {
        'biz': biz, 'stats': stats, 'upcoming': upcoming, 'today': today,
    })


@login_required(login_url='/accounts/login/')
def services(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            BookingService.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', ''),
                duration_minutes=request.POST.get('duration_minutes', 60) or 60,
                price=request.POST.get('price', 0) or 0,
                currency=request.POST.get('currency', 'USD').strip(),
                category=request.POST.get('category', '').strip(),
                color=request.POST.get('color', '#3b82f6').strip(),
                buffer_before=request.POST.get('buffer_before', 0) or 0,
                buffer_after=request.POST.get('buffer_after', 0) or 0,
            )
            messages.success(request, 'Service created.')
        elif action == 'delete':
            BookingService.objects.filter(pk=request.POST.get('service_id'), business=biz).delete()
            messages.success(request, 'Service deleted.')
        return redirect('booking:services', slug=slug)
    all_services = BookingService.objects.filter(business=biz)
    return render(request, 'booking/services.html', {'biz': biz, 'services': all_services})


@login_required(login_url='/accounts/login/')
def bookings(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    qs = Booking.objects.filter(business=biz).select_related('service', 'staff').order_by('-date', '-start_time')
    if status_filter:
        qs = qs.filter(status=status_filter)
    if date_filter:
        qs = qs.filter(date=date_filter)
    all_services = BookingService.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            service = get_object_or_404(BookingService, pk=request.POST.get('service'), business=biz)
            from datetime import datetime, timedelta
            start_time = request.POST.get('start_time')
            if start_time:
                start_dt = datetime.strptime(start_time, '%H:%M')
                end_dt = start_dt + timedelta(minutes=service.duration_minutes)
                end_time = end_dt.strftime('%H:%M')
            else:
                end_time = request.POST.get('end_time', '')
            Booking.objects.create(
                business=biz,
                service=service,
                staff_id=request.POST.get('staff') or None,
                customer_name=request.POST.get('customer_name', '').strip(),
                customer_email=request.POST.get('customer_email', '').strip(),
                customer_phone=request.POST.get('customer_phone', '').strip(),
                date=request.POST.get('date'),
                start_time=start_time,
                end_time=end_time,
                notes=request.POST.get('notes', ''),
                price=service.price,
            )
            messages.success(request, 'Booking created.')
        return redirect('booking:bookings', slug=slug)
    return render(request, 'booking/bookings.html', {
        'biz': biz, 'bookings': qs, 'services': all_services,
        'status_filter': status_filter, 'date_filter': date_filter,
    })


@login_required(login_url='/accounts/login/')
def booking_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    booking = get_object_or_404(Booking, pk=pk, business=biz)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            booking.status = request.POST.get('status', booking.status)
            if booking.status == 'cancelled':
                booking.cancellation_reason = request.POST.get('cancellation_reason', '')
            booking.save()
            messages.success(request, f'Booking {booking.get_status_display()}.')
        elif action == 'delete':
            booking.delete()
            messages.success(request, 'Booking deleted.')
            return redirect('booking:bookings', slug=slug)
        return redirect('booking:booking_detail', slug=slug, pk=pk)
    return render(request, 'booking/booking_detail.html', {
        'biz': biz, 'booking': booking,
    })
