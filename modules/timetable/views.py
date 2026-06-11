from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hub.models import BusinessInstance, BusinessEmployee
from .models import Room, TimeSlot, ClassSession, ScheduleException, DAYS_OF_WEEK


def _tt_check(slug, user, min_level=1):
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
def timetable_home(request, slug):
    biz, emp, level = _tt_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    sessions = ClassSession.objects.filter(business=biz, is_active=True).select_related('instructor__user', 'room', 'time_slot')

    # Build weekly grid: {day: [sessions]}
    grid = {day: [] for day, _ in DAYS_OF_WEEK}
    for s in sessions:
        if s.time_slot:
            grid[s.time_slot.day_of_week].append(s)

    class_groups = sessions.values_list('class_group', flat=True).distinct().order_by('class_group')
    class_filter = request.GET.get('class_group', '')
    if class_filter:
        sessions = sessions.filter(class_group=class_filter)
        grid = {day: [] for day, _ in DAYS_OF_WEEK}
        for s in sessions:
            if s.time_slot:
                grid[s.time_slot.day_of_week].append(s)

    return render(request, 'timetable/home.html', {
        'biz': biz, 'access_level': level,
        'grid': grid, 'days': DAYS_OF_WEEK,
        'class_groups': class_groups, 'class_filter': class_filter,
        'stats': {
            'rooms': Room.objects.filter(business=biz, is_active=True).count(),
            'slots': TimeSlot.objects.filter(business=biz).count(),
            'sessions': ClassSession.objects.filter(business=biz, is_active=True).count(),
        },
    })


@login_required
def room_list(request, slug):
    biz, emp, level = _tt_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'create_room':
            Room.objects.create(
                business=biz,
                name=request.POST.get('name', ''),
                room_type=request.POST.get('room_type', 'classroom'),
                capacity=request.POST.get('capacity') or None,
                building=request.POST.get('building', ''),
                floor=request.POST.get('floor', ''),
                equipment=request.POST.get('equipment', ''),
            )
            messages.success(request, 'Room added.')
        elif action == 'toggle_room':
            r = get_object_or_404(Room, pk=request.POST.get('room_id'), business=biz)
            r.is_active = not r.is_active
            r.save()
            messages.success(request, f"Room {'activated' if r.is_active else 'deactivated'}.")
        return redirect('timetable:room_list', slug=slug)

    rooms = Room.objects.filter(business=biz)
    return render(request, 'timetable/room_list.html', {
        'biz': biz, 'access_level': level, 'rooms': rooms,
        'room_types': Room.ROOM_TYPE,
    })


@login_required
def session_manage(request, slug):
    biz, emp, level = _tt_check(slug, request.user, min_level=3)
    if not level:
        return redirect('timetable:timetable_home', slug=slug)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_slot':
            TimeSlot.objects.create(
                business=biz,
                label=request.POST.get('slot_label', ''),
                day_of_week=request.POST.get('day_of_week', ''),
                start_time=request.POST.get('start_time', ''),
                end_time=request.POST.get('end_time', ''),
            )
            messages.success(request, 'Time slot created.')

        elif action == 'create_session':
            ClassSession.objects.create(
                business=biz,
                subject=request.POST.get('subject', ''),
                class_group=request.POST.get('class_group', ''),
                instructor_id=request.POST.get('instructor_id') or None,
                room_id=request.POST.get('room_id') or None,
                time_slot_id=request.POST.get('time_slot_id') or None,
                effective_from=request.POST.get('effective_from', ''),
                effective_until=request.POST.get('effective_until') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Session scheduled.')

        elif action == 'delete_session':
            ClassSession.objects.filter(pk=request.POST.get('session_id'), business=biz).delete()
            messages.success(request, 'Session removed.')

        elif action == 'add_exception':
            sess = get_object_or_404(ClassSession, pk=request.POST.get('session_id'), business=biz)
            ScheduleException.objects.create(
                session=sess,
                exception_date=request.POST.get('exception_date', ''),
                reason=request.POST.get('reason', ''),
                is_cancelled='is_cancelled' in request.POST,
                substitute_instructor_id=request.POST.get('sub_instructor_id') or None,
            )
            messages.success(request, 'Exception recorded.')

        return redirect('timetable:session_manage', slug=slug)

    sessions = ClassSession.objects.filter(business=biz).select_related('instructor__user', 'room', 'time_slot')
    time_slots = TimeSlot.objects.filter(business=biz)
    rooms = Room.objects.filter(business=biz, is_active=True)
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'timetable/session_manage.html', {
        'biz': biz, 'access_level': level,
        'sessions': sessions, 'time_slots': time_slots,
        'rooms': rooms, 'employees': employees,
        'days': DAYS_OF_WEEK,
    })
