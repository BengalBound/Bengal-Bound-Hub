from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from hub.models import BusinessInstance, BusinessEmployee
from .models import TravelClient, Itinerary, ItineraryItem, TravelBooking


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
def tcrm_home(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    total_clients = TravelClient.objects.filter(business=biz).count()
    active_itineraries = Itinerary.objects.filter(business=biz).exclude(
        status__in=['cancelled', 'completed']
    ).count()
    total_bookings = TravelBooking.objects.filter(business=biz).count()
    pending_commission = TravelBooking.objects.filter(
        business=biz, status__in=['confirmed', 'ticketed']
    ).aggregate(total=Sum('commission_amount'))['total'] or 0

    recent_itineraries = Itinerary.objects.filter(business=biz).select_related('client')[:8]

    return render(request, 'travel_crm/home.html', {
        'biz': biz,
        'access_level': level,
        'stats': {
            'total_clients': total_clients,
            'active_itineraries': active_itineraries,
            'total_bookings': total_bookings,
            'pending_commission': pending_commission,
        },
        'recent_itineraries': recent_itineraries,
    })


@login_required
def client_list(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'add_client':
            assigned_id = request.POST.get('assigned_to_id')
            assigned = BusinessEmployee.objects.filter(pk=assigned_id, business=biz).first() if assigned_id else emp
            client = TravelClient.objects.create(
                business=biz,
                full_name=request.POST.get('full_name', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                nationality=request.POST.get('nationality', ''),
                passport_number=request.POST.get('passport_number', ''),
                date_of_birth=request.POST.get('date_of_birth') or None,
                preferred_airline=request.POST.get('preferred_airline', ''),
                frequent_flyer_number=request.POST.get('frequent_flyer_number', ''),
                dietary_requirements=request.POST.get('dietary_requirements', ''),
                notes=request.POST.get('notes', ''),
                assigned_to=assigned,
            )
            messages.success(request, f'Client "{client.full_name}" added.')
            return redirect('travel_crm:client_detail', slug=slug, client_id=client.pk)
        return redirect('travel_crm:client_list', slug=slug)

    assigned_filter = request.GET.get('assigned', '')
    clients = TravelClient.objects.filter(business=biz).select_related('assigned_to__user')
    if assigned_filter:
        clients = clients.filter(assigned_to_id=assigned_filter)

    agents = BusinessEmployee.objects.filter(business=biz, is_active=True)
    return render(request, 'travel_crm/client_list.html', {
        'biz': biz,
        'access_level': level,
        'clients': clients,
        'agents': agents,
        'assigned_filter': assigned_filter,
    })


@login_required
def client_detail(request, slug, client_id):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    client = get_object_or_404(TravelClient, pk=client_id, business=biz)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')

        if action == 'add_itinerary':
            itin = Itinerary.objects.create(
                business=biz,
                client=client,
                title=request.POST.get('title', ''),
                destination=request.POST.get('destination', ''),
                start_date=request.POST.get('start_date', ''),
                end_date=request.POST.get('end_date', ''),
                status=request.POST.get('status', 'draft'),
                total_budget=request.POST.get('total_budget') or None,
                currency=request.POST.get('currency', 'USD'),
                notes=request.POST.get('notes', ''),
                created_by=emp,
            )
            messages.success(request, f'Itinerary "{itin.title}" created.')

        elif action == 'add_booking':
            booking = TravelBooking.objects.create(
                business=biz,
                client=client,
                itinerary=Itinerary.objects.filter(
                    pk=request.POST.get('itinerary_id'), business=biz
                ).first() if request.POST.get('itinerary_id') else None,
                booking_reference=request.POST.get('booking_reference', ''),
                booking_type=request.POST.get('booking_type', 'other'),
                supplier=request.POST.get('supplier', ''),
                travel_date=request.POST.get('travel_date', ''),
                return_date=request.POST.get('return_date') or None,
                amount=request.POST.get('amount', 0),
                currency=request.POST.get('currency', 'USD'),
                status=request.POST.get('status', 'pending'),
                commission_amount=request.POST.get('commission_amount', 0),
                notes=request.POST.get('notes', ''),
                created_by=emp,
            )
            messages.success(request, f'Booking "{booking.booking_reference}" added.')

        return redirect('travel_crm:client_detail', slug=slug, client_id=client_id)

    itineraries = Itinerary.objects.filter(client=client).order_by('-created_at')
    bookings = TravelBooking.objects.filter(client=client).order_by('-created_at')

    return render(request, 'travel_crm/client_detail.html', {
        'biz': biz,
        'access_level': level,
        'client': client,
        'itineraries': itineraries,
        'bookings': bookings,
        'itin_statuses': Itinerary.STATUS_CHOICES,
        'booking_types': TravelBooking.BOOKING_TYPE_CHOICES,
        'booking_statuses': TravelBooking.STATUS_CHOICES,
    })


@login_required
def itinerary_list(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    status_filter = request.GET.get('status', '')
    itineraries = Itinerary.objects.filter(business=biz).select_related('client', 'created_by__user')
    if status_filter:
        itineraries = itineraries.filter(status=status_filter)

    return render(request, 'travel_crm/itinerary_list.html', {
        'biz': biz,
        'access_level': level,
        'itineraries': itineraries,
        'status_filter': status_filter,
        'statuses': Itinerary.STATUS_CHOICES,
    })


@login_required
def itinerary_detail(request, slug, itin_id):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    itin = get_object_or_404(Itinerary, pk=itin_id, business=biz)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')

        if action == 'add_item':
            ItineraryItem.objects.create(
                itinerary=itin,
                day_number=request.POST.get('day_number', 1),
                item_type=request.POST.get('item_type', 'other'),
                title=request.POST.get('title', ''),
                description=request.POST.get('description', ''),
                supplier=request.POST.get('supplier', ''),
                confirmation_code=request.POST.get('confirmation_code', ''),
                start_time=request.POST.get('start_time') or None,
                end_time=request.POST.get('end_time') or None,
                cost=request.POST.get('cost') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Item added to itinerary.')

        elif action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(Itinerary.STATUS_CHOICES):
                itin.status = new_status
                itin.save(update_fields=['status'])
                messages.success(request, f'Status updated to {itin.get_status_display()}.')

        elif action == 'delete_item':
            item = get_object_or_404(ItineraryItem, pk=request.POST.get('item_id'), itinerary=itin)
            item.delete()
            messages.success(request, 'Item removed.')

        return redirect('travel_crm:itinerary_detail', slug=slug, itin_id=itin_id)

    items = itin.items.all()
    return render(request, 'travel_crm/itinerary_detail.html', {
        'biz': biz,
        'access_level': level,
        'itin': itin,
        'items': items,
        'statuses': Itinerary.STATUS_CHOICES,
        'item_types': ItineraryItem.ITEM_TYPE_CHOICES,
    })


@login_required
def booking_list(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'update_booking_status':
            booking = get_object_or_404(TravelBooking, pk=request.POST.get('booking_id'), business=biz)
            new_status = request.POST.get('status')
            if new_status in dict(TravelBooking.STATUS_CHOICES):
                booking.status = new_status
                booking.save(update_fields=['status'])
                messages.success(request, f'Booking {booking.booking_reference} updated.')
        return redirect('travel_crm:booking_list', slug=slug)

    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    bookings = TravelBooking.objects.filter(business=biz).select_related('client', 'created_by__user')
    if type_filter:
        bookings = bookings.filter(booking_type=type_filter)
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    return render(request, 'travel_crm/booking_list.html', {
        'biz': biz,
        'access_level': level,
        'bookings': bookings,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'booking_types': TravelBooking.BOOKING_TYPE_CHOICES,
        'booking_statuses': TravelBooking.STATUS_CHOICES,
    })
