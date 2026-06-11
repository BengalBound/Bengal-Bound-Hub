from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from hub.models import BusinessInstance, BusinessEmployee
from .models import GroupRFP, GroupBlock, RoomingListEntry, GroupContract


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
def gb_home(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    rfps = GroupRFP.objects.filter(business=biz)
    total_rfps = rfps.count()
    active_rfps = rfps.exclude(status__in=['cancelled', 'declined']).count()
    confirmed_rfps = rfps.filter(status='confirmed').count()
    rooms_blocked = GroupBlock.objects.filter(rfp__business=biz).aggregate(
        total=Sum('rooms_blocked')
    )['total'] or 0

    recent_rfps = rfps.select_related('assigned_to__user')[:8]

    return render(request, 'group_bookings/home.html', {
        'biz': biz,
        'access_level': level,
        'stats': {
            'total_rfps': total_rfps,
            'active_rfps': active_rfps,
            'confirmed_rfps': confirmed_rfps,
            'rooms_blocked': rooms_blocked,
        },
        'recent_rfps': recent_rfps,
    })


@login_required
def rfp_list(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'create_rfp':
            rfp = GroupRFP.objects.create(
                business=biz,
                group_name=request.POST.get('group_name', ''),
                contact_name=request.POST.get('contact_name', ''),
                contact_email=request.POST.get('contact_email', ''),
                contact_phone=request.POST.get('contact_phone', ''),
                event_type=request.POST.get('event_type', 'conference'),
                arrival_date=request.POST.get('arrival_date', ''),
                departure_date=request.POST.get('departure_date', ''),
                rooms_required=request.POST.get('rooms_required', 1),
                adults=request.POST.get('adults', 1),
                children=request.POST.get('children', 0),
                special_requirements=request.POST.get('special_requirements', ''),
                notes=request.POST.get('notes', ''),
                assigned_to=emp,
            )
            messages.success(request, f'RFP "{rfp.rfp_number}" created.')
            return redirect('group_bookings:rfp_detail', slug=slug, rfp_id=rfp.pk)
        return redirect('group_bookings:rfp_list', slug=slug)

    status_filter = request.GET.get('status', '')
    rfps = GroupRFP.objects.filter(business=biz).select_related('assigned_to__user')
    if status_filter:
        rfps = rfps.filter(status=status_filter)

    return render(request, 'group_bookings/rfp_list.html', {
        'biz': biz,
        'access_level': level,
        'rfps': rfps,
        'status_filter': status_filter,
        'statuses': GroupRFP.STATUS_CHOICES,
        'event_types': GroupRFP.EVENT_TYPE_CHOICES,
    })


@login_required
def rfp_detail(request, slug, rfp_id):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    rfp = get_object_or_404(GroupRFP, pk=rfp_id, business=biz)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_block' and level >= 2:
            GroupBlock.objects.create(
                rfp=rfp,
                room_type_name=request.POST.get('room_type_name', ''),
                rooms_blocked=request.POST.get('rooms_blocked', 1),
                rate_per_night=request.POST.get('rate_per_night', 0),
                currency=request.POST.get('currency', 'USD'),
                release_date=request.POST.get('release_date') or None,
                is_confirmed='is_confirmed' in request.POST,
            )
            messages.success(request, 'Room block added.')

        elif action == 'add_guest' and level >= 2:
            RoomingListEntry.objects.create(
                rfp=rfp,
                guest_name=request.POST.get('guest_name', ''),
                room_type_name=request.POST.get('room_type_name', ''),
                check_in=request.POST.get('check_in', ''),
                check_out=request.POST.get('check_out', ''),
                special_requests=request.POST.get('special_requests', ''),
            )
            messages.success(request, 'Guest added to rooming list.')

        elif action == 'assign_room' and level >= 2:
            entry = get_object_or_404(RoomingListEntry, pk=request.POST.get('entry_id'), rfp=rfp)
            entry.room_number = request.POST.get('room_number', '')
            entry.is_assigned = True
            entry.save(update_fields=['room_number', 'is_assigned'])
            messages.success(request, f'Room assigned to {entry.guest_name}.')

        elif action == 'update_status' and level >= 3:
            new_status = request.POST.get('status')
            if new_status in dict(GroupRFP.STATUS_CHOICES):
                rfp.status = new_status
                rfp.save(update_fields=['status'])
                messages.success(request, f'Status updated to {rfp.get_status_display()}.')

        elif action == 'save_contract' and level >= 3:
            contract, created = GroupContract.objects.get_or_create(rfp=rfp)
            contract.deposit_amount = request.POST.get('deposit_amount', 0)
            contract.deposit_due_date = request.POST.get('deposit_due_date') or None
            contract.deposit_paid = 'deposit_paid' in request.POST
            contract.total_value = request.POST.get('total_value', 0)
            contract.currency = request.POST.get('currency', 'USD')
            contract.cancellation_policy = request.POST.get('cancellation_policy', '')
            contract.attrition_pct = request.POST.get('attrition_pct', 20)
            contract.signed = 'signed' in request.POST
            contract.signed_date = request.POST.get('signed_date') or None
            contract.notes = request.POST.get('notes', '')
            contract.save()
            messages.success(request, 'Contract saved.')

        return redirect('group_bookings:rfp_detail', slug=slug, rfp_id=rfp_id)

    blocks = rfp.blocks.all()
    rooming = rfp.rooming_list.all()
    contract = getattr(rfp, 'contract', None)

    return render(request, 'group_bookings/rfp_detail.html', {
        'biz': biz,
        'access_level': level,
        'rfp': rfp,
        'blocks': blocks,
        'rooming': rooming,
        'contract': contract,
        'statuses': GroupRFP.STATUS_CHOICES,
        'event_types': GroupRFP.EVENT_TYPE_CHOICES,
    })


@login_required
def rooming_list(request, slug, rfp_id):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    rfp = get_object_or_404(GroupRFP, pk=rfp_id, business=biz)
    entries = rfp.rooming_list.all()

    return render(request, 'group_bookings/rooming_list.html', {
        'biz': biz,
        'access_level': level,
        'rfp': rfp,
        'entries': entries,
    })
