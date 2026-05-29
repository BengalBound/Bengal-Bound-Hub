from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from hub.views import _get_business_for_user
from hub.access import require_employee
from .models import BizCalendar, CalendarEvent, EventAttendee


@require_employee
def calendar_home(request, slug):
    biz = _get_business_for_user(slug, request.user)
    calendars = BizCalendar.objects.filter(business=biz)
    if not calendars.exists():
        default_cal = BizCalendar.objects.create(
            business=biz, name='Team Calendar', is_default=True, created_by=request.user
        )
        calendars = BizCalendar.objects.filter(business=biz)

    now = timezone.now()
    upcoming = CalendarEvent.objects.filter(
        calendar__business=biz,
        start_datetime__gte=now,
        status__in=['confirmed', 'tentative']
    ).order_by('start_datetime')[:20]

    return render(request, 'business_calendar/home.html', {
        'biz': biz, 'calendars': calendars, 'upcoming': upcoming,
        'now': now, 'current_business': biz,
    })


@require_employee
def calendar_events_api(request, slug):
    """JSON endpoint for FullCalendar or custom JS calendar."""
    biz = _get_business_for_user(slug, request.user)
    events = CalendarEvent.objects.filter(calendar__business=biz, status__in=['confirmed', 'tentative'])
    data = []
    for ev in events:
        data.append({
            'id': ev.pk,
            'title': ev.title,
            'start': ev.start_datetime.isoformat(),
            'end': ev.end_datetime.isoformat(),
            'color': ev.color or ev.calendar.color,
            'allDay': ev.all_day,
            'location': ev.location,
        })
    return JsonResponse(data, safe=False)


@require_employee
def event_create(request, slug):
    biz = _get_business_for_user(slug, request.user)
    calendars = BizCalendar.objects.filter(business=biz)
    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True).select_related('user')

    if request.method == 'POST':
        cal_id = request.POST.get('calendar_id')
        calendar = get_object_or_404(BizCalendar, pk=cal_id, business=biz)
        title = request.POST.get('title', '').strip()
        start = request.POST.get('start_datetime')
        end = request.POST.get('end_datetime')
        all_day = request.POST.get('all_day') == '1'

        if not title or not start or not end:
            messages.error(request, 'Title, start, and end are required.')
        else:
            event = CalendarEvent.objects.create(
                calendar=calendar,
                title=title,
                description=request.POST.get('description', ''),
                location=request.POST.get('location', ''),
                start_datetime=start,
                end_datetime=end,
                all_day=all_day,
                recurrence=request.POST.get('recurrence', 'none'),
                color=request.POST.get('color', ''),
                created_by=request.user,
            )
            EventAttendee.objects.create(event=event, user=request.user, rsvp='accepted')
            for emp_id in request.POST.getlist('attendee_ids'):
                try:
                    emp = BusinessEmployee.objects.get(pk=emp_id, business=biz)
                    if emp.user and emp.user != request.user:
                        EventAttendee.objects.get_or_create(event=event, user=emp.user)
                except Exception:
                    pass
            messages.success(request, f'Event "{title}" created.')
            return redirect('business_calendar:calendar_home', slug=slug)

    return render(request, 'business_calendar/event_form.html', {
        'biz': biz, 'calendars': calendars, 'employees': employees,
        'recurrences': CalendarEvent.RECURRENCE, 'current_business': biz,
    })


@require_employee
def event_detail(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    event = get_object_or_404(CalendarEvent, pk=pk, calendar__business=biz)
    attendees = event.attendees.select_related('user').all()
    my_rsvp = attendees.filter(user=request.user).first()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'rsvp' and my_rsvp:
            my_rsvp.rsvp = request.POST.get('rsvp', 'accepted')
            my_rsvp.save()
            messages.success(request, 'RSVP updated.')
        elif action == 'delete' and event.created_by == request.user:
            event.delete()
            messages.success(request, 'Event deleted.')
            return redirect('business_calendar:calendar_home', slug=slug)
        return redirect('business_calendar:event_detail', slug=slug, pk=pk)

    return render(request, 'business_calendar/event_detail.html', {
        'biz': biz, 'event': event, 'attendees': attendees, 'my_rsvp': my_rsvp, 'current_business': biz,
    })


@require_employee
def calendar_manage(request, slug):
    biz = _get_business_for_user(slug, request.user)
    calendars = BizCalendar.objects.filter(business=biz)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            BizCalendar.objects.create(
                business=biz,
                name=request.POST.get('name', 'New Calendar'),
                color=request.POST.get('color', '#c084fc'),
                created_by=request.user,
            )
            messages.success(request, 'Calendar created.')
        elif action == 'delete':
            BizCalendar.objects.filter(pk=request.POST.get('cal_id'), business=biz).exclude(is_default=True).delete()
            messages.success(request, 'Calendar deleted.')
        return redirect('business_calendar:calendar_manage', slug=slug)
    return render(request, 'business_calendar/manage.html', {'biz': biz, 'calendars': calendars, 'current_business': biz})
