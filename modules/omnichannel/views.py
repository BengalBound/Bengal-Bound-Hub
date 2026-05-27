from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from hub.models import BusinessInstance, BusinessEmployee
from .models import SalesChannel, ChannelListing, ChannelSyncLog


def _oc_check(slug, user, min_level=1):
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
def omnichannel_home(request, slug):
    biz, emp, level = _oc_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    channels = SalesChannel.objects.filter(business=biz)
    active_channels = channels.filter(is_active=True)
    listings = ChannelListing.objects.filter(business=biz)
    recent_syncs = ChannelSyncLog.objects.filter(channel__business=biz).select_related('channel')[:10]

    stats = {
        'channels': channels.count(),
        'active_channels': active_channels.count(),
        'listings': listings.count(),
        'synced': listings.filter(is_synced=True).count(),
    }

    return render(request, 'omnichannel/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats,
        'channels': channels, 'recent_syncs': recent_syncs,
    })


@login_required
def channel_list(request, slug):
    biz, emp, level = _oc_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'create_channel':
            SalesChannel.objects.create(
                business=biz,
                name=request.POST['name'],
                channel_type=request.POST.get('channel_type', 'other'),
                url=request.POST.get('url', ''),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Channel added.')
        elif action == 'toggle_channel':
            ch = get_object_or_404(SalesChannel, pk=request.POST.get('channel_id'), business=biz)
            ch.is_active = not ch.is_active
            ch.save(update_fields=['is_active'])
        return redirect('omnichannel:channel_list', slug=slug)

    channels = SalesChannel.objects.filter(business=biz)
    channel_types = SalesChannel.CHANNEL_TYPES
    return render(request, 'omnichannel/channel_list.html', {
        'biz': biz, 'access_level': level, 'channels': channels,
        'channel_types': channel_types,
    })


@login_required
def channel_detail(request, slug, channel_id):
    biz, emp, level = _oc_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    channel = get_object_or_404(SalesChannel, pk=channel_id, business=biz)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_listing':
            ChannelListing.objects.create(
                business=biz,
                channel=channel,
                product_name=request.POST['product_name'],
                sku=request.POST.get('sku', ''),
                channel_sku=request.POST.get('channel_sku', ''),
                listed_price=request.POST.get('listed_price') or None,
                stock_qty=request.POST.get('stock_qty', 0),
            )
            messages.success(request, 'Listing added.')
        elif action == 'sync':
            synced = channel.listings.count()
            channel.listings.update(is_synced=True, last_synced_at=timezone.now())
            ChannelSyncLog.objects.create(
                channel=channel, items_synced=synced, status='success',
                notes=f'Manual sync by {emp.user.get_full_name()}',
            )
            messages.success(request, f'Synced {synced} listings.')
        elif action == 'delete_listing':
            ChannelListing.objects.filter(pk=request.POST.get('listing_id'), business=biz).delete()
        return redirect('omnichannel:channel_detail', slug=slug, channel_id=channel_id)

    listings = channel.listings.all()
    sync_logs = channel.sync_logs.all()[:15]
    return render(request, 'omnichannel/channel_detail.html', {
        'biz': biz, 'access_level': level, 'channel': channel,
        'listings': listings, 'sync_logs': sync_logs,
    })
