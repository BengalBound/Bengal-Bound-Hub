from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone

from hub.views import _get_business_for_user
from hub.access import get_access_level
from .models import Carrier, Route, Shipment, ShipmentEvent, FreightQuote


def _tms_check(slug, user, min_level=2):
    biz = _get_business_for_user(slug, user)
    if not biz:
        return None, HttpResponseForbidden()
    if get_access_level(biz, user) < min_level:
        return None, HttpResponseForbidden()
    return biz, None


def _next_shipment_number(business):
    last = Shipment.objects.filter(business=business).order_by('-pk').first()
    num = int(last.shipment_number) + 1 if last else 1
    return str(num).zfill(5)


def _next_quote_number(business):
    last = FreightQuote.objects.filter(business=business).order_by('-pk').first()
    num = int(last.quote_number) + 1 if last else 1
    return str(num).zfill(5)


@login_required(login_url='/accounts/login/')
def tms_dashboard(request, slug):
    biz, err = _tms_check(slug, request.user)
    if err:
        return err

    status_counts = {}
    for s, _ in Shipment.STATUS:
        status_counts[s] = Shipment.objects.filter(business=biz, status=s).count()

    active = Shipment.objects.filter(
        business=biz,
        status__in=['booked', 'pickup_ready', 'in_transit', 'at_hub', 'out_for_delivery']
    ).select_related('carrier', 'route')[:10]

    delayed = Shipment.objects.filter(business=biz, status='delayed').count()
    carriers = Carrier.objects.filter(business=biz, is_active=True)

    return render(request, 'tms/dashboard.html', {
        'biz': biz,
        'status_counts': status_counts,
        'active': active,
        'delayed': delayed,
        'carriers': carriers,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def shipment_list(request, slug):
    biz, err = _tms_check(slug, request.user)
    if err:
        return err

    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    search = request.GET.get('q', '').strip()

    shipments = Shipment.objects.filter(business=biz).select_related('carrier', 'route')
    if status_filter:
        shipments = shipments.filter(status=status_filter)
    if type_filter:
        shipments = shipments.filter(shipment_type=type_filter)
    if search:
        shipments = (
            shipments.filter(shipment_number__icontains=search) |
            Shipment.objects.filter(business=biz, customer_name__icontains=search) |
            Shipment.objects.filter(business=biz, tracking_number__icontains=search)
        )

    return render(request, 'tms/shipment_list.html', {
        'biz': biz,
        'shipments': shipments,
        'statuses': Shipment.STATUS,
        'shipment_types': Shipment.SHIPMENT_TYPE,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search': search,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def shipment_create(request, slug):
    biz, err = _tms_check(slug, request.user, min_level=3)
    if err:
        return err

    if request.method == 'POST':
        carrier_id = request.POST.get('carrier_id', '')
        route_id = request.POST.get('route_id', '')

        shipment = Shipment.objects.create(
            business=biz,
            shipment_number=_next_shipment_number(biz),
            shipment_type=request.POST.get('shipment_type', 'outbound'),
            priority=request.POST.get('priority', 'standard'),
            carrier_id=int(carrier_id) if carrier_id else None,
            route_id=int(route_id) if route_id else None,
            origin_name=request.POST.get('origin_name', '').strip(),
            origin_address=request.POST.get('origin_address', '').strip(),
            destination_name=request.POST.get('destination_name', '').strip(),
            destination_address=request.POST.get('destination_address', '').strip(),
            customer_name=request.POST.get('customer_name', '').strip(),
            customer_reference=request.POST.get('customer_reference', '').strip(),
            purchase_order_ref=request.POST.get('purchase_order_ref', '').strip(),
            cargo_description=request.POST.get('cargo_description', '').strip(),
            pieces=request.POST.get('pieces', '') or None,
            weight_kg=request.POST.get('weight_kg', '') or None,
            volume_m3=request.POST.get('volume_m3', '') or None,
            is_hazmat=bool(request.POST.get('is_hazmat')),
            requires_refrigeration=bool(request.POST.get('requires_refrigeration')),
            tracking_number=request.POST.get('tracking_number', '').strip(),
            scheduled_pickup=request.POST.get('scheduled_pickup', '') or None,
            scheduled_delivery=request.POST.get('scheduled_delivery', '') or None,
            freight_cost=request.POST.get('freight_cost', '') or None,
            insurance_value=request.POST.get('insurance_value', '') or None,
            notes=request.POST.get('notes', '').strip(),
            created_by=request.user,
            status='booked',
        )
        ShipmentEvent.objects.create(
            shipment=shipment, event_type='booked',
            note='Shipment created.', recorded_by=request.user,
        )
        messages.success(request, f"Shipment SHP-{shipment.shipment_number} created.")
        return redirect('tms:shipment_detail', slug=slug, shipment_id=shipment.pk)

    carriers = Carrier.objects.filter(business=biz, is_active=True)
    routes = Route.objects.filter(business=biz, is_active=True)
    return render(request, 'tms/shipment_form.html', {
        'biz': biz,
        'carriers': carriers,
        'routes': routes,
        'shipment_types': Shipment.SHIPMENT_TYPE,
        'priorities': Shipment.PRIORITY,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def shipment_detail(request, slug, shipment_id):
    biz, err = _tms_check(slug, request.user)
    if err:
        return err

    shipment = get_object_or_404(Shipment, pk=shipment_id, business=biz)
    level = get_access_level(biz, request.user)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'status' and level >= 3:
            new_status = request.POST.get('status', shipment.status)
            shipment.status = new_status
            if new_status == 'in_transit' and not shipment.actual_pickup:
                shipment.actual_pickup = timezone.now()
            if new_status == 'delivered' and not shipment.actual_delivery:
                shipment.actual_delivery = timezone.now()
            shipment.save()
            ShipmentEvent.objects.create(
                shipment=shipment,
                event_type=new_status if new_status in dict(ShipmentEvent.EVENT_TYPES) else 'note',
                location=request.POST.get('location', '').strip(),
                note=request.POST.get('note', '').strip(),
                recorded_by=request.user,
            )
            messages.success(request, f"Status updated to {shipment.get_status_display()}.")

        elif action == 'add_event' and level >= 2:
            ShipmentEvent.objects.create(
                shipment=shipment,
                event_type=request.POST.get('event_type', 'note'),
                location=request.POST.get('location', '').strip(),
                note=request.POST.get('note', '').strip(),
                timestamp=request.POST.get('timestamp', '') or timezone.now(),
                recorded_by=request.user,
            )
            messages.success(request, "Tracking event added.")

        elif action == 'update' and level >= 3:
            shipment.tracking_number = request.POST.get('tracking_number', shipment.tracking_number).strip()
            shipment.freight_cost = request.POST.get('freight_cost', '') or shipment.freight_cost
            shipment.notes = request.POST.get('notes', shipment.notes).strip()
            shipment.save(update_fields=['tracking_number', 'freight_cost', 'notes'])
            messages.success(request, "Shipment updated.")

        return redirect('tms:shipment_detail', slug=slug, shipment_id=shipment_id)

    events = shipment.events.all()
    return render(request, 'tms/shipment_detail.html', {
        'biz': biz,
        'shipment': shipment,
        'events': events,
        'statuses': Shipment.STATUS,
        'event_types': ShipmentEvent.EVENT_TYPES,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def carrier_list(request, slug):
    biz, err = _tms_check(slug, request.user)
    if err:
        return err

    level = get_access_level(biz, request.user)

    if request.method == 'POST' and level >= 4:
        action = request.POST.get('action', 'create')
        if action == 'create':
            Carrier.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                carrier_type=request.POST.get('carrier_type', 'road'),
                contact_name=request.POST.get('contact_name', '').strip(),
                contact_phone=request.POST.get('contact_phone', '').strip(),
                contact_email=request.POST.get('contact_email', '').strip(),
                account_number=request.POST.get('account_number', '').strip(),
                notes=request.POST.get('notes', '').strip(),
            )
            messages.success(request, "Carrier added.")
        elif action == 'toggle':
            c_id = request.POST.get('carrier_id', '')
            if c_id:
                c = get_object_or_404(Carrier, pk=int(c_id), business=biz)
                c.is_active = not c.is_active
                c.save(update_fields=['is_active'])
        return redirect('tms:carriers', slug=slug)

    carriers = Carrier.objects.filter(business=biz)
    return render(request, 'tms/carrier_list.html', {
        'biz': biz,
        'carriers': carriers,
        'carrier_types': Carrier.TYPES,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def route_list(request, slug):
    biz, err = _tms_check(slug, request.user)
    if err:
        return err

    level = get_access_level(biz, request.user)

    if request.method == 'POST' and level >= 4:
        carrier_id = request.POST.get('preferred_carrier_id', '')
        Route.objects.create(
            business=biz,
            name=request.POST.get('name', '').strip(),
            origin=request.POST.get('origin', '').strip(),
            destination=request.POST.get('destination', '').strip(),
            distance_km=request.POST.get('distance_km', '') or None,
            estimated_hours=request.POST.get('estimated_hours', '') or None,
            preferred_carrier_id=int(carrier_id) if carrier_id else None,
            base_cost=request.POST.get('base_cost', '') or None,
            notes=request.POST.get('notes', '').strip(),
        )
        messages.success(request, "Route added.")
        return redirect('tms:routes', slug=slug)

    routes = Route.objects.filter(business=biz).select_related('preferred_carrier')
    carriers = Carrier.objects.filter(business=biz, is_active=True)
    return render(request, 'tms/route_list.html', {
        'biz': biz,
        'routes': routes,
        'carriers': carriers,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def quote_list(request, slug):
    biz, err = _tms_check(slug, request.user)
    if err:
        return err

    level = get_access_level(biz, request.user)

    if request.method == 'POST' and level >= 3:
        carrier_id = request.POST.get('carrier_id', '')
        FreightQuote.objects.create(
            business=biz,
            quote_number=_next_quote_number(biz),
            customer_name=request.POST.get('customer_name', '').strip(),
            customer_email=request.POST.get('customer_email', '').strip(),
            origin=request.POST.get('origin', '').strip(),
            destination=request.POST.get('destination', '').strip(),
            cargo_description=request.POST.get('cargo_description', '').strip(),
            weight_kg=request.POST.get('weight_kg', '') or None,
            volume_m3=request.POST.get('volume_m3', '') or None,
            carrier_id=int(carrier_id) if carrier_id else None,
            quoted_price=request.POST.get('quoted_price', 0),
            transit_days=request.POST.get('transit_days', '') or None,
            valid_until=request.POST.get('valid_until', '') or None,
            notes=request.POST.get('notes', '').strip(),
            created_by=request.user,
        )
        messages.success(request, "Freight quote created.")
        return redirect('tms:quotes', slug=slug)

    quotes = FreightQuote.objects.filter(business=biz).select_related('carrier')
    carriers = Carrier.objects.filter(business=biz, is_active=True)
    return render(request, 'tms/quote_list.html', {
        'biz': biz,
        'quotes': quotes,
        'carriers': carriers,
        'quote_statuses': FreightQuote.STATUS,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })
