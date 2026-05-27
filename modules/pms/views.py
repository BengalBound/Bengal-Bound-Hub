from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from hub.models import BusinessInstance, BusinessEmployee
from .models import (
    Room, RoomType, GuestProfile, Reservation, FolioCharge, HousekeepingTask
)


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
def pms_home(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    today = timezone.localdate()
    rooms = Room.objects.filter(business=biz)
    total_rooms = rooms.count()
    available_rooms = rooms.filter(status='available').count()
    occupied = rooms.filter(status='occupied').count()

    reservations_today = Reservation.objects.filter(
        business=biz, check_in_date=today
    ).count()
    arrivals = Reservation.objects.filter(
        business=biz, check_in_date=today, status='confirmed'
    ).count()
    departures = Reservation.objects.filter(
        business=biz, check_out_date=today, status='checked_in'
    ).count()
    recent_reservations = Reservation.objects.filter(business=biz).select_related(
        'guest', 'room', 'room_type'
    )[:8]

    return render(request, 'pms/home.html', {
        'biz': biz,
        'access_level': level,
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied': occupied,
        'reservations_today': reservations_today,
        'arrivals': arrivals,
        'departures': departures,
        'recent_reservations': recent_reservations,
        'today': today,
    })


@login_required
def room_list(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'update_status':
            room_id = request.POST.get('room_id')
            new_status = request.POST.get('status')
            room = get_object_or_404(Room, pk=room_id, business=biz)
            if new_status in dict(Room.STATUS_CHOICES):
                room.status = new_status
                room.save(update_fields=['status'])
                messages.success(request, f"Room {room.room_number} status updated to {room.get_status_display()}.")
        return redirect('pms:room_list', slug=slug)

    status_filter = request.GET.get('status', '')
    rooms = Room.objects.filter(business=biz).select_related('room_type')
    if status_filter:
        rooms = rooms.filter(status=status_filter)

    return render(request, 'pms/room_list.html', {
        'biz': biz,
        'access_level': level,
        'rooms': rooms,
        'status_filter': status_filter,
        'status_choices': Room.STATUS_CHOICES,
    })


@login_required
def reservation_list(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    reservations = Reservation.objects.filter(business=biz).select_related('guest', 'room', 'room_type')

    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if status_filter:
        reservations = reservations.filter(status=status_filter)
    if date_from:
        reservations = reservations.filter(check_in_date__gte=date_from)
    if date_to:
        reservations = reservations.filter(check_out_date__lte=date_to)

    return render(request, 'pms/reservation_list.html', {
        'biz': biz,
        'access_level': level,
        'reservations': reservations,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': Reservation.STATUS_CHOICES,
    })


@login_required
def reservation_add(request, slug):
    biz, emp, level = _check(slug, request.user, min_level=2)
    if not level:
        return redirect('pms:reservation_list', slug=slug)

    guests = GuestProfile.objects.filter(business=biz)
    rooms = Room.objects.filter(business=biz).select_related('room_type')
    room_types = RoomType.objects.filter(business=biz)

    if request.method == 'POST':
        guest_id = request.POST.get('guest_id')
        guest = get_object_or_404(GuestProfile, pk=guest_id, business=biz)

        room_id = request.POST.get('room_id')
        room = Room.objects.filter(pk=room_id, business=biz).first() if room_id else None

        room_type_id = request.POST.get('room_type_id')
        room_type = RoomType.objects.filter(pk=room_type_id, business=biz).first() if room_type_id else None

        check_in_date = request.POST['check_in_date']
        check_out_date = request.POST['check_out_date']
        rate_per_night = request.POST.get('rate_per_night', 0)

        reservation = Reservation(
            business=biz,
            guest=guest,
            room=room,
            room_type=room_type,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=request.POST.get('adults', 1),
            children=request.POST.get('children', 0),
            status=request.POST.get('status', 'confirmed'),
            rate_per_night=rate_per_night,
            currency=request.POST.get('currency', 'USD'),
            source=request.POST.get('source', 'direct'),
            notes=request.POST.get('notes', ''),
            created_by=emp,
        )
        # Calculate total_amount before save so nights property is available
        from datetime import date
        try:
            ci = date.fromisoformat(check_in_date)
            co = date.fromisoformat(check_out_date)
            nights = (co - ci).days
            reservation.total_amount = float(rate_per_night) * nights if nights > 0 else 0
        except (ValueError, TypeError):
            reservation.total_amount = 0

        reservation.save()
        messages.success(request, f"Reservation {reservation.reservation_number} created.")
        return redirect('pms:reservation_detail', slug=slug, res_id=reservation.pk)

    return render(request, 'pms/reservation_form.html', {
        'biz': biz,
        'access_level': level,
        'guests': guests,
        'rooms': rooms,
        'room_types': room_types,
        'status_choices': Reservation.STATUS_CHOICES,
        'source_choices': Reservation.SOURCE_CHOICES,
    })


@login_required
def reservation_detail(request, slug, res_id):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    reservation = get_object_or_404(Reservation, pk=res_id, business=biz)
    folio_charges = reservation.folio_charges.select_related('posted_by')

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')

        if action == 'check_in':
            if reservation.status == 'confirmed':
                reservation.status = 'checked_in'
                reservation.save(update_fields=['status'])
                if reservation.room:
                    reservation.room.status = 'occupied'
                    reservation.room.save(update_fields=['status'])
                messages.success(request, f"Guest checked in to reservation {reservation.reservation_number}.")

        elif action == 'check_out':
            if reservation.status == 'checked_in':
                reservation.status = 'checked_out'
                reservation.save(update_fields=['status'])
                if reservation.room:
                    reservation.room.status = 'dirty'
                    reservation.room.save(update_fields=['status'])
                messages.success(request, f"Guest checked out from reservation {reservation.reservation_number}.")

        elif action == 'add_charge':
            FolioCharge.objects.create(
                reservation=reservation,
                charge_type=request.POST.get('charge_type', 'other'),
                description=request.POST['description'],
                amount=request.POST['amount'],
                currency=request.POST.get('currency', reservation.currency),
                posted_by=emp,
            )
            messages.success(request, "Charge posted to folio.")

        elif action == 'cancel':
            if reservation.status not in ('checked_out', 'cancelled'):
                reservation.status = 'cancelled'
                reservation.save(update_fields=['status'])
                messages.success(request, f"Reservation {reservation.reservation_number} cancelled.")

        return redirect('pms:reservation_detail', slug=slug, res_id=res_id)

    return render(request, 'pms/reservation_detail.html', {
        'biz': biz,
        'access_level': level,
        'reservation': reservation,
        'folio_charges': folio_charges,
        'charge_type_choices': FolioCharge.CHARGE_TYPE_CHOICES,
    })


@login_required
def guest_list(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'add_guest':
            GuestProfile.objects.create(
                business=biz,
                full_name=request.POST['full_name'],
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                nationality=request.POST.get('nationality', ''),
                passport_number=request.POST.get('passport_number', ''),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, "Guest profile created.")
        return redirect('pms:guest_list', slug=slug)

    guests = GuestProfile.objects.filter(business=biz)
    return render(request, 'pms/guest_list.html', {
        'biz': biz,
        'access_level': level,
        'guests': guests,
    })


@login_required
def housekeeping(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    today = timezone.localdate()
    staff = BusinessEmployee.objects.filter(business=biz, is_active=True)
    rooms = Room.objects.filter(business=biz)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')

        if action == 'add_task':
            room_id = request.POST.get('room_id')
            room = get_object_or_404(Room, pk=room_id, business=biz)
            assigned_id = request.POST.get('assigned_to_id')
            assigned = BusinessEmployee.objects.filter(pk=assigned_id, business=biz).first() if assigned_id else None
            HousekeepingTask.objects.create(
                business=biz,
                room=room,
                task_type=request.POST.get('task_type', 'stayover'),
                status='pending',
                assigned_to=assigned,
                scheduled_date=request.POST.get('scheduled_date', today),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, "Housekeeping task created.")

        elif action == 'update_task':
            task_id = request.POST.get('task_id')
            task = get_object_or_404(HousekeepingTask, pk=task_id, business=biz)
            new_status = request.POST.get('status', task.status)
            if new_status in dict(HousekeepingTask.STATUS_CHOICES):
                task.status = new_status
                if new_status == 'done' and not task.completed_at:
                    task.completed_at = timezone.now()
                task.save(update_fields=['status', 'completed_at'])
                messages.success(request, f"Task updated to {task.get_status_display()}.")

        return redirect('pms:housekeeping', slug=slug)

    tasks = HousekeepingTask.objects.filter(
        business=biz, scheduled_date__gte=today
    ).select_related('room', 'assigned_to').order_by('scheduled_date', 'room__room_number')

    return render(request, 'pms/housekeeping.html', {
        'biz': biz,
        'access_level': level,
        'tasks': tasks,
        'rooms': rooms,
        'staff': staff,
        'today': today,
        'task_type_choices': HousekeepingTask.TASK_TYPE_CHOICES,
        'status_choices': HousekeepingTask.STATUS_CHOICES,
    })
