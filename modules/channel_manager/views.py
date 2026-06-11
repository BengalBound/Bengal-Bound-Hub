from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from hub.models import BusinessInstance, BusinessEmployee
from .models import Channel, RatePlan, ChannelRate, AvailabilityBlock, ChannelSyncLog


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
def cm_home(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    channels = Channel.objects.filter(business=biz)
    last_sync = ChannelSyncLog.objects.filter(business=biz).first()
    stats = {
        'total_channels': channels.count(),
        'active_channels': channels.filter(is_active=True).count(),
        'rate_plans': RatePlan.objects.filter(business=biz).count(),
        'last_sync': last_sync,
    }
    recent_logs = ChannelSyncLog.objects.filter(business=biz).select_related('channel')[:10]

    return render(request, 'channel_manager/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats, 'recent_logs': recent_logs,
    })


@login_required
def channel_list(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_channel':
            channel = Channel.objects.create(
                business=biz,
                name=request.POST.get('name', ''),
                channel_type=request.POST.get('channel_type', 'ota'),
                api_endpoint=request.POST.get('api_endpoint', ''),
                api_key=request.POST.get('api_key', ''),
                commission_pct=request.POST.get('commission_pct') or 0,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, f'Channel "{channel.name}" added.')
        elif action == 'toggle_channel':
            channel = get_object_or_404(Channel, pk=request.POST.get('channel_id'), business=biz)
            channel.is_active = not channel.is_active
            channel.save(update_fields=['is_active'])
            state = 'activated' if channel.is_active else 'deactivated'
            messages.success(request, f'Channel "{channel.name}" {state}.')
        return redirect('channel_manager:channels', slug=slug)

    channels = Channel.objects.filter(business=biz)
    return render(request, 'channel_manager/channels.html', {
        'biz': biz, 'access_level': level, 'channels': channels,
        'channel_types': Channel.CHANNEL_TYPES,
    })


@login_required
def rate_plans(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_plan':
            plan = RatePlan.objects.create(
                business=biz,
                name=request.POST.get('name', ''),
                code=request.POST.get('code', ''),
                description=request.POST.get('description', ''),
                meal_plan=request.POST.get('meal_plan', 'ro'),
                is_refundable=request.POST.get('is_refundable') == 'on',
                min_stay=request.POST.get('min_stay') or 1,
            )
            messages.success(request, f'Rate plan "{plan.name}" added.')
        elif action == 'add_rate':
            channel = get_object_or_404(Channel, pk=request.POST.get('channel_id'), business=biz)
            rate_plan = get_object_or_404(RatePlan, pk=request.POST.get('rate_plan_id'), business=biz)
            ChannelRate.objects.create(
                channel=channel,
                rate_plan=rate_plan,
                room_type_name=request.POST.get('room_type_name', ''),
                rate_amount=request.POST.get('rate_amount', ''),
                currency=request.POST.get('currency', 'USD'),
                valid_from=request.POST.get('valid_from', ''),
                valid_to=request.POST.get('valid_to', ''),
            )
            messages.success(request, 'Channel rate added.')
        return redirect('channel_manager:rates', slug=slug)

    plans = RatePlan.objects.filter(business=biz)
    channels = Channel.objects.filter(business=biz, is_active=True)
    channel_rates = ChannelRate.objects.filter(channel__business=biz).select_related('channel', 'rate_plan')
    return render(request, 'channel_manager/rates.html', {
        'biz': biz, 'access_level': level, 'plans': plans,
        'channels': channels, 'channel_rates': channel_rates,
        'meal_plans': RatePlan.MEAL_PLANS,
    })


@login_required
def availability(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    today = timezone.now().date()
    end_date = today + timedelta(days=30)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'set_availability':
            block_date = request.POST.get('date', '')
            room_type = request.POST.get('room_type_name', '')
            block, created = AvailabilityBlock.objects.get_or_create(
                business=biz,
                room_type_name=room_type,
                date=block_date,
                defaults={
                    'available_rooms': request.POST.get('available_rooms') or 0,
                    'sold_rooms': request.POST.get('sold_rooms') or 0,
                }
            )
            if not created:
                block.available_rooms = request.POST.get('available_rooms') or 0
                block.sold_rooms = request.POST.get('sold_rooms') or 0
                block.save(update_fields=['available_rooms', 'sold_rooms'])
            messages.success(request, f'Availability updated for {room_type} on {block_date}.')
        return redirect('channel_manager:availability', slug=slug)

    blocks = AvailabilityBlock.objects.filter(
        business=biz, date__gte=today, date__lte=end_date
    ).order_by('date', 'room_type_name')
    return render(request, 'channel_manager/availability.html', {
        'biz': biz, 'access_level': level, 'blocks': blocks,
        'today': today, 'end_date': end_date,
    })


@login_required
def sync_log(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'log_sync':
            channel_id = request.POST.get('channel_id')
            channel = Channel.objects.filter(pk=channel_id, business=biz).first() if channel_id else None
            log = ChannelSyncLog.objects.create(
                business=biz,
                channel=channel,
                sync_type=request.POST.get('sync_type', 'full'),
                status=request.POST.get('status', 'success'),
                message=request.POST.get('message', ''),
                records_synced=request.POST.get('records_synced') or 0,
            )
            messages.success(request, f'Sync log recorded ({log.get_sync_type_display()}).')
        return redirect('channel_manager:sync_log', slug=slug)

    logs = ChannelSyncLog.objects.filter(business=biz).select_related('channel')
    channels = Channel.objects.filter(business=biz)
    return render(request, 'channel_manager/sync_log.html', {
        'biz': biz, 'access_level': level, 'logs': logs, 'channels': channels,
        'sync_types': ChannelSyncLog.SYNC_TYPES, 'sync_statuses': ChannelSyncLog.SYNC_STATUS,
    })
