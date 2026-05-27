from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import Announcement, AnnouncementRead, AnnouncementComment


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    now = timezone.now()
    announcements = Announcement.objects.filter(business=biz, is_active=True, publish_at__lte=now).order_by('-is_pinned', '-publish_at')
    read_ids = AnnouncementRead.objects.filter(user=request.user, announcement__in=announcements).values_list('announcement_id', flat=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Announcement.objects.create(
                business=biz, title=request.POST.get('title', '').strip(),
                content=request.POST.get('content', ''),
                announcement_type=request.POST.get('announcement_type', 'general'),
                priority=request.POST.get('priority', 'normal'),
                is_pinned='is_pinned' in request.POST,
                created_by=request.user,
            )
            messages.success(request, 'Announcement posted.')
        elif action == 'mark_read':
            ann = get_object_or_404(Announcement, pk=request.POST.get('ann_id'), business=biz)
            AnnouncementRead.objects.get_or_create(announcement=ann, user=request.user)
        return redirect('announcements:index', slug=slug)
    return render(request, 'announcements/index.html', {'biz': biz, 'announcements': announcements, 'read_ids': list(read_ids)})


@login_required(login_url='/accounts/login/')
def detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    ann = get_object_or_404(Announcement, pk=pk, business=biz)
    AnnouncementRead.objects.get_or_create(announcement=ann, user=request.user)
    comments = ann.comments.select_related('author').order_by('created_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'comment' and ann.allow_comments:
            AnnouncementComment.objects.create(announcement=ann, author=request.user, content=request.POST.get('content', '').strip())
            messages.success(request, 'Comment added.')
        elif action == 'delete' and ann.created_by == request.user:
            ann.delete()
            messages.success(request, 'Announcement deleted.')
            return redirect('announcements:index', slug=slug)
        return redirect('announcements:detail', slug=slug, pk=pk)
    return render(request, 'announcements/detail.html', {'biz': biz, 'announcement': ann, 'comments': comments})
