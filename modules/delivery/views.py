from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import DeliveryZone, Driver, DeliveryOrder, DeliveryRoute


def _biz(slug, user):
    return _get_business_for_user(slug, user)


def _next_order_number(biz):
    count = DeliveryOrder.objects.filter(business=biz).count() + 1
    return f"{count:05d}"


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    today = timezone.now().date()
    pending_orders = DeliveryOrder.objects.filter(business=biz, status='pending').count()
    in_transit = DeliveryOrder.objects.filter(business=biz, status='in_transit').count()
    delivered_today = DeliveryOrder.objects.filter(business=biz, delivered_at__date=today).count()
    total_drivers = Driver.objects.filter(business=biz, is_active=True).count()
    recent_orders = DeliveryOrder.objects.filter(business=biz).select_related('driver', 'zone').order_by('-created_at')[:10]
    return render(request, 'delivery/index.html', {
        'biz': biz,
        'pending_orders': pending_orders,
        'in_transit': in_transit,
        'delivered_today': delivered_today,
        'total_drivers': total_drivers,
        'recent_orders': recent_orders,
    })


@login_required(login_url='/accounts/login/')
def delivery_orders(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status_filter = request.GET.get('status', '')
    qs = DeliveryOrder.objects.filter(business=biz).select_related('driver', 'zone').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    drivers = Driver.objects.filter(business=biz, is_active=True)
    zones = DeliveryZone.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            DeliveryOrder.objects.create(
                business=biz,
                order_number=_next_order_number(biz),
                priority=request.POST.get('priority', 'normal'),
                driver_id=request.POST.get('driver') or None,
                zone_id=request.POST.get('zone') or None,
                pickup_address=request.POST.get('pickup_address', '').strip(),
                pickup_contact=request.POST.get('pickup_contact', '').strip(),
                pickup_phone=request.POST.get('pickup_phone', '').strip(),
                delivery_address=request.POST.get('delivery_address', '').strip(),
                delivery_contact=request.POST.get('delivery_contact', '').strip(),
                delivery_phone=request.POST.get('delivery_phone', '').strip(),
                scheduled_date=request.POST.get('scheduled_date') or today,
                description=request.POST.get('description', ''),
                special_instructions=request.POST.get('special_instructions', ''),
                delivery_fee=request.POST.get('delivery_fee', 0) or 0,
                created_by=request.user,
            )
            messages.success(request, 'Delivery order created.')
        return redirect('delivery:delivery_orders', slug=slug)
    today = timezone.now().date()
    return render(request, 'delivery/delivery_orders.html', {
        'biz': biz, 'orders': qs, 'drivers': drivers, 'zones': zones,
        'status_filter': status_filter, 'today': today,
    })


@login_required(login_url='/accounts/login/')
def order_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    order = get_object_or_404(DeliveryOrder, pk=pk, business=biz)
    drivers = Driver.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            order.status = request.POST.get('status', order.status)
            order.driver_id = request.POST.get('driver') or order.driver_id
            if order.status == 'delivered':
                order.delivered_at = timezone.now()
            elif order.status == 'failed':
                order.failure_reason = request.POST.get('failure_reason', '')
            order.save()
            messages.success(request, f'Status updated to {order.get_status_display()}.')
        elif action == 'delete':
            order.delete()
            messages.success(request, 'Delivery order deleted.')
            return redirect('delivery:delivery_orders', slug=slug)
        return redirect('delivery:order_detail', slug=slug, pk=pk)
    return render(request, 'delivery/order_detail.html', {
        'biz': biz, 'order': order, 'drivers': drivers,
    })


@login_required(login_url='/accounts/login/')
def drivers(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Driver.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                phone=request.POST.get('phone', '').strip(),
                email=request.POST.get('email', '').strip(),
                license_number=request.POST.get('license_number', '').strip(),
                vehicle_type=request.POST.get('vehicle_type', '').strip(),
                vehicle_plate=request.POST.get('vehicle_plate', '').strip(),
            )
            messages.success(request, 'Driver added.')
        elif action == 'update_status':
            driver = get_object_or_404(Driver, pk=request.POST.get('driver_id'), business=biz)
            driver.status = request.POST.get('status', driver.status)
            driver.save(update_fields=['status'])
            messages.success(request, 'Driver status updated.')
        elif action == 'delete':
            Driver.objects.filter(pk=request.POST.get('driver_id'), business=biz).delete()
            messages.success(request, 'Driver removed.')
        return redirect('delivery:drivers', slug=slug)
    all_drivers = Driver.objects.filter(business=biz)
    return render(request, 'delivery/drivers.html', {'biz': biz, 'drivers': all_drivers})


@login_required(login_url='/accounts/login/')
def routes(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    all_routes = DeliveryRoute.objects.filter(business=biz).select_related('driver').order_by('-date')
    drivers = Driver.objects.filter(business=biz, is_active=True)
    pending_orders = DeliveryOrder.objects.filter(business=biz, status='pending')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            route = DeliveryRoute.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                driver_id=request.POST.get('driver') or None,
                date=request.POST.get('date') or timezone.now().date(),
                notes=request.POST.get('notes', ''),
            )
            order_ids = request.POST.getlist('orders')
            if order_ids:
                route.orders.set(DeliveryOrder.objects.filter(pk__in=order_ids, business=biz))
            messages.success(request, f'Route "{route.name}" created.')
        return redirect('delivery:routes', slug=slug)
    return render(request, 'delivery/routes.html', {
        'biz': biz, 'routes': all_routes, 'drivers': drivers, 'pending_orders': pending_orders,
    })
