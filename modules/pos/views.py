from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import POSConfig, POSSession, POSOrder, POSOrderItem


def _biz(slug, user):
    return _get_business_for_user(slug, user)


def _next_order_number(session):
    count = session.orders.count() + 1
    return f"{session.pk:04d}-{count:04d}"


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    configs = POSConfig.objects.filter(business=biz, is_active=True)
    open_sessions = POSSession.objects.filter(config__business=biz, status='open').select_related('config', 'cashier')
    stats = {
        'configs': configs.count(),
        'open_sessions': open_sessions.count(),
        'orders_today': POSOrder.objects.filter(session__config__business=biz, created_at__date=timezone.now().date()).count(),
        'revenue_today': sum(
            o.total for o in POSOrder.objects.filter(
                session__config__business=biz,
                created_at__date=timezone.now().date(),
                status='paid'
            )
        ),
    }
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_config':
            POSConfig.objects.create(
                business=biz,
                name=request.POST.get('name', 'Main Register').strip(),
                tax_rate=request.POST.get('tax_rate', 0) or 0,
                currency=request.POST.get('currency', 'USD').strip(),
                allow_discount=request.POST.get('allow_discount') == 'on',
                allow_refund=request.POST.get('allow_refund') == 'on',
            )
            messages.success(request, 'POS register created.')
        elif action == 'open_session':
            cfg = get_object_or_404(POSConfig, pk=request.POST.get('config_id'), business=biz)
            existing = POSSession.objects.filter(config=cfg, status='open').first()
            if existing:
                messages.warning(request, 'This register already has an open session.')
            else:
                POSSession.objects.create(
                    config=cfg, cashier=request.user,
                    opening_cash=request.POST.get('opening_cash', 0) or 0,
                )
                messages.success(request, f'Session opened for {cfg.name}.')
        return redirect('pos:index', slug=slug)
    return render(request, 'pos/index.html', {
        'biz': biz, 'configs': configs, 'open_sessions': open_sessions, 'stats': stats,
    })


@login_required(login_url='/accounts/login/')
def session_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    session = get_object_or_404(POSSession, pk=pk, config__business=biz)
    orders = session.orders.order_by('-created_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'close_session':
            session.status = 'closed'
            session.closing_cash = request.POST.get('closing_cash', 0) or 0
            session.closed_at = timezone.now()
            session.save(update_fields=['status', 'closing_cash', 'closed_at'])
            messages.success(request, 'Session closed.')
            return redirect('pos:index', slug=slug)
        elif action == 'new_order':
            order = POSOrder.objects.create(
                session=session,
                order_number=_next_order_number(session),
                customer_name=request.POST.get('customer_name', '').strip(),
            )
            return redirect('pos:order_detail', slug=slug, session_pk=pk, order_pk=order.pk)
    return render(request, 'pos/session_detail.html', {
        'biz': biz, 'session': session, 'orders': orders,
    })


@login_required(login_url='/accounts/login/')
def order_detail(request, slug, session_pk, order_pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    session = get_object_or_404(POSSession, pk=session_pk, config__business=biz)
    order = get_object_or_404(POSOrder, pk=order_pk, session=session)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_item':
            item = POSOrderItem(
                order=order,
                product_name=request.POST.get('product_name', '').strip(),
                quantity=request.POST.get('quantity', 1) or 1,
                unit_price=request.POST.get('unit_price', 0) or 0,
                discount_pct=request.POST.get('discount_pct', 0) or 0,
            )
            item.save()
            order.recalculate()
            messages.success(request, 'Item added.')
        elif action == 'remove_item':
            POSOrderItem.objects.filter(pk=request.POST.get('item_id'), order=order).delete()
            order.recalculate()
        elif action == 'pay':
            order.payment_method = request.POST.get('payment_method', 'cash')
            order.amount_tendered = request.POST.get('amount_tendered', order.total) or order.total
            order.change_due = float(order.amount_tendered) - float(order.total)
            order.status = 'paid'
            order.paid_at = timezone.now()
            order.save()
            messages.success(request, f'Order {order.order_number} paid.')
            return redirect('pos:session_detail', slug=slug, pk=session_pk)
        elif action == 'cancel':
            order.status = 'cancelled'
            order.save(update_fields=['status'])
            messages.info(request, 'Order cancelled.')
            return redirect('pos:session_detail', slug=slug, pk=session_pk)
        return redirect('pos:order_detail', slug=slug, session_pk=session_pk, order_pk=order_pk)
    return render(request, 'pos/order_detail.html', {
        'biz': biz, 'session': session, 'order': order, 'items': order.items.all(),
    })
