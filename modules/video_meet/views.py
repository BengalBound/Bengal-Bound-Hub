from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
import datetime

from hub.views import _get_business_for_user
from hub.access import require_employee, require_manager
from .models import MeetingRoom, Meeting, MeetingAttendee


@require_employee
def meet_home(request, slug):
    biz = _get_business_for_user(slug, request.user)
    now = timezone.now()
    upcoming = Meeting.objects.filter(business=biz, start_time__gte=now, status='scheduled').order_by('start_time')[:10]
    past = Meeting.objects.filter(business=biz, end_time__lt=now).order_by('-start_time')[:10]
    rooms = MeetingRoom.objects.filter(business=biz, is_active=True)
    my_meetings = Meeting.objects.filter(attendees__user=request.user, business=biz, start_time__gte=now).order_by('start_time')[:5]
    return render(request, 'video_meet/home.html', {
        'biz': biz, 'upcoming': upcoming, 'past': past, 'rooms': rooms,
        'my_meetings': my_meetings, 'now': now, 'current_business': biz,
    })


@require_employee
def meet_schedule(request, slug):
    biz = _get_business_for_user(slug, request.user)
    rooms = MeetingRoom.objects.filter(business=biz, is_active=True)
    from accounts.models import User
    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True).select_related('user')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        start_str = request.POST.get('start_time')
        end_str = request.POST.get('end_time')
        room_id = request.POST.get('room_id')
        description = request.POST.get('description', '').strip()
        attendee_ids = request.POST.getlist('attendee_ids')
        ext_url = request.POST.get('meeting_url', '').strip()

        if not title or not start_str or not end_str:
            messages.error(request, 'Title, start time, and end time are required.')
        else:
            room = MeetingRoom.objects.filter(pk=room_id, business=biz).first() if room_id else None
            meeting = Meeting.objects.create(
                business=biz,
                room=room,
                title=title,
                description=description,
                organizer=request.user,
                start_time=start_str,
                end_time=end_str,
                meeting_url=ext_url,
            )
            MeetingAttendee.objects.create(meeting=meeting, user=request.user, status='accepted')
            for uid in attendee_ids:
                try:
                    emp = BusinessEmployee.objects.get(pk=uid, business=biz)
                    if emp.user and emp.user != request.user:
                        MeetingAttendee.objects.get_or_create(meeting=meeting, user=emp.user)
                except Exception:
                    pass
            messages.success(request, f'Meeting "{title}" scheduled.')
            return redirect('video_meet:meet_detail', slug=slug, pk=meeting.pk)

    return render(request, 'video_meet/schedule.html', {
        'biz': biz, 'rooms': rooms, 'employees': employees, 'current_business': biz,
    })


@require_employee
def meet_detail(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    meeting = get_object_or_404(Meeting, pk=pk, business=biz)
    attendees = meeting.attendees.select_related('user').all()
    my_rsvp = attendees.filter(user=request.user).first()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'rsvp' and my_rsvp:
            my_rsvp.status = request.POST.get('status', 'accepted')
            my_rsvp.save()
            messages.success(request, 'RSVP updated.')
        elif action == 'cancel' and meeting.organizer == request.user:
            meeting.status = 'cancelled'
            meeting.save(update_fields=['status'])
            messages.info(request, 'Meeting cancelled.')
        return redirect('video_meet:meet_detail', slug=slug, pk=pk)

    return render(request, 'video_meet/detail.html', {
        'biz': biz, 'meeting': meeting, 'attendees': attendees,
        'my_rsvp': my_rsvp, 'current_business': biz,
    })


@require_manager
def room_manage(request, slug):
    biz = _get_business_for_user(slug, request.user)
    rooms = MeetingRoom.objects.filter(business=biz)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            MeetingRoom.objects.create(
                business=biz,
                name=request.POST.get('name', 'Meeting Room'),
                description=request.POST.get('description', ''),
                capacity=request.POST.get('capacity', 20),
                created_by=request.user,
            )
            messages.success(request, 'Meeting room created.')
        elif action == 'delete':
            MeetingRoom.objects.filter(pk=request.POST.get('room_id'), business=biz).delete()
            messages.success(request, 'Room deleted.')
        return redirect('video_meet:room_manage', slug=slug)
    return render(request, 'video_meet/rooms.html', {'biz': biz, 'rooms': rooms, 'current_business': biz})
