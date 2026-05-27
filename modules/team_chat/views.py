import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import Channel, ChannelMember, Message, DirectMessage


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def channel_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    channels = Channel.objects.filter(business=biz, is_archived=False)

    # Auto-join user to all public channels they're not yet in
    for ch in channels.filter(channel_type='public'):
        ChannelMember.objects.get_or_create(channel=ch, user=request.user)

    my_channels = channels.filter(members__user=request.user)
    active_channel_id = request.GET.get('ch')
    active_channel = None
    messages = []

    if active_channel_id:
        active_channel = get_object_or_404(Channel, id=active_channel_id, business=biz)
        messages = active_channel.messages.filter(is_deleted=False).select_related('author')[:100]
        # Mark as read
        member = active_channel.members.filter(user=request.user).first()
        if member:
            member.mark_read()

    return render(request, 'team_chat/chat.html', {
        'biz': biz,
        'channels': my_channels,
        'all_channels': channels,
        'active_channel': active_channel,
        'messages': messages,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
@require_POST
def channel_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    name = request.POST.get('name', '').strip().lower().replace(' ', '-')
    if not name:
        return redirect('team_chat:channel_list', slug=slug)

    channel, created = Channel.objects.get_or_create(
        business=biz, name=name,
        defaults={
            'topic': request.POST.get('topic', '').strip(),
            'channel_type': request.POST.get('channel_type', 'public'),
            'created_by': request.user,
        }
    )
    if created:
        ChannelMember.objects.create(channel=channel, user=request.user, is_admin=True)

    return redirect(f'{request.path}?ch={channel.id}' if '?' not in request.path else f'?ch={channel.id}')


@login_required(login_url='/accounts/login/')
@require_POST
def message_send(request, slug, channel_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    channel = get_object_or_404(Channel, id=channel_id, business=biz)
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Empty message'}, status=400)

    msg = Message.objects.create(channel=channel, author=request.user, content=content)

    # Mark sender as read
    member = channel.members.filter(user=request.user).first()
    if member:
        member.mark_read()

    return JsonResponse({
        'id': msg.id,
        'content': msg.content,
        'author': request.user.get_full_name() or request.user.email,
        'created_at': msg.created_at.strftime('%H:%M'),
        'date': msg.created_at.strftime('%b %d'),
    })


@login_required(login_url='/accounts/login/')
def message_poll(request, slug, channel_id):
    """Long-poll endpoint: returns messages after given message ID."""
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    channel = get_object_or_404(Channel, id=channel_id, business=biz)
    after_id = request.GET.get('after', 0)

    msgs = channel.messages.filter(id__gt=after_id, is_deleted=False).select_related('author')[:50]
    return JsonResponse({'messages': [
        {
            'id': m.id,
            'content': m.content,
            'author': m.author.get_full_name() or m.author.email if m.author else 'Unknown',
            'created_at': m.created_at.strftime('%H:%M'),
            'is_mine': m.author_id == request.user.id,
        }
        for m in msgs
    ]})


@login_required(login_url='/accounts/login/')
@require_POST
def message_delete(request, slug, message_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    msg = get_object_or_404(Message, id=message_id, channel__business=biz)
    if msg.author != request.user and biz.owner != request.user:
        return HttpResponseForbidden()

    msg.is_deleted = True
    msg.content = ''
    msg.save(update_fields=['is_deleted', 'content'])
    return JsonResponse({'ok': True})


@login_required(login_url='/accounts/login/')
@require_POST
def reaction_toggle(request, slug, message_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    msg = get_object_or_404(Message, id=message_id, channel__business=biz)
    from .models import MessageReaction
    emoji = request.POST.get('emoji', '')
    if not emoji:
        return JsonResponse({'error': 'No emoji'}, status=400)

    obj, created = MessageReaction.objects.get_or_create(message=msg, user=request.user, emoji=emoji)
    if not created:
        obj.delete()

    count = MessageReaction.objects.filter(message=msg, emoji=emoji).count()
    return JsonResponse({'emoji': emoji, 'count': count, 'active': created})
