from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hub.models import BusinessInstance, BusinessEmployee
from .models import B2BCustomer, B2BOrder, B2BOrderLine


def _b2b_check(slug, user, min_level=1):
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
def b2b_home(request, slug):
    biz, emp, level = _b2b_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    customers = B2BCustomer.objects.filter(business=biz)
    orders = B2BOrder.objects.filter(business=biz).select_related('customer')
    active_orders = orders.exclude(status__in=['delivered', 'cancelled'])

    total_revenue = sum(o.total_amount for o in orders.filter(status='delivered'))
    recent_orders = orders[:8]

    stats = {
        'customers': customers.count(),
        'active_customers': customers.filter(is_active=True).count(),
        'active_orders': active_orders.count(),
        'total_revenue': total_revenue,
    }

    return render(request, 'b2b_portal/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats,
        'recent_orders': recent_orders,
    })


@login_required
def customer_list(request, slug):
    biz, emp, level = _b2b_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        B2BCustomer.objects.create(
            business=biz,
            company_name=request.POST.get('company_name', ''),
            contact_name=request.POST.get('contact_name', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            price_tier=request.POST.get('price_tier', 'standard'),
            credit_limit=request.POST.get('credit_limit') or None,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'B2B customer added.')
        return redirect('b2b_portal:customer_list', slug=slug)

    customers = B2BCustomer.objects.filter(business=biz)
    tier_filter = request.GET.get('tier', '')
    if tier_filter:
        customers = customers.filter(price_tier=tier_filter)

    return render(request, 'b2b_portal/customer_list.html', {
        'biz': biz, 'access_level': level, 'customers': customers,
        'tier_filter': tier_filter, 'price_tiers': B2BCustomer.PRICE_TIERS,
    })


@login_required
def customer_detail(request, slug, customer_id):
    biz, emp, level = _b2b_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    customer = get_object_or_404(B2BCustomer, pk=customer_id, business=biz)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'create_order':
            B2BOrder.objects.create(
                business=biz,
                customer=customer,
                reference_no=request.POST.get('reference_no', ''),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Order created.')
        elif action == 'toggle_active' and level >= 3:
            customer.is_active = not customer.is_active
            customer.save(update_fields=['is_active'])
        return redirect('b2b_portal:customer_detail', slug=slug, customer_id=customer_id)

    orders = customer.orders.all()
    return render(request, 'b2b_portal/customer_detail.html', {
        'biz': biz, 'access_level': level, 'customer': customer, 'orders': orders,
    })


@login_required
def order_list(request, slug):
    biz, emp, level = _b2b_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    orders = B2BOrder.objects.filter(business=biz).select_related('customer')
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, 'b2b_portal/order_list.html', {
        'biz': biz, 'access_level': level, 'orders': orders,
        'status_filter': status_filter, 'statuses': B2BOrder.STATUS,
    })


@login_required
def order_detail(request, slug, order_id):
    biz, emp, level = _b2b_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    order = get_object_or_404(B2BOrder, pk=order_id, business=biz)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'add_line':
            B2BOrderLine.objects.create(
                order=order,
                product_name=request.POST.get('product_name', ''),
                sku=request.POST.get('sku', ''),
                qty=request.POST.get('qty', 1),
                unit_price=request.POST.get('unit_price', 0),
                unit=request.POST.get('unit', ''),
            )
            messages.success(request, 'Line item added.')
        elif action == 'delete_line':
            B2BOrderLine.objects.filter(pk=request.POST.get('line_id'), order=order).delete()
        elif action == 'update_status' and level >= 3:
            new_status = request.POST.get('status')
            if new_status in dict(B2BOrder.STATUS):
                order.status = new_status
                order.save(update_fields=['status'])
                messages.success(request, f'Status updated to {order.get_status_display()}.')
        return redirect('b2b_portal:order_detail', slug=slug, order_id=order_id)

    lines = order.lines.all()
    return render(request, 'b2b_portal/order_detail.html', {
        'biz': biz, 'access_level': level, 'order': order,
        'lines': lines, 'statuses': B2BOrder.STATUS,
    })
