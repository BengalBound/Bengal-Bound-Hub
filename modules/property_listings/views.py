from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hub.models import BusinessInstance, BusinessEmployee
from .models import Property, PropertyShowing


def _pl_check(slug, user, min_level=1):
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
def property_home(request, slug):
    biz, emp, level = _pl_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    props = Property.objects.filter(business=biz)
    stats = {
        'total': props.count(),
        'active': props.filter(status='active').count(),
        'under_contract': props.filter(status='under_contract').count(),
        'sold': props.filter(status='sold').count(),
    }
    recent = props[:8]
    upcoming_showings = PropertyShowing.objects.filter(
        property__business=biz, status='scheduled'
    ).select_related('property', 'agent').order_by('scheduled_at')[:10]

    return render(request, 'property_listings/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats,
        'recent': recent, 'upcoming_showings': upcoming_showings,
    })


@login_required
def property_list(request, slug):
    biz, emp, level = _pl_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    props = Property.objects.filter(business=biz)
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    agent_filter = request.GET.get('agent', '')

    if type_filter:
        props = props.filter(property_type=type_filter)
    if status_filter:
        props = props.filter(status=status_filter)
    if agent_filter:
        props = props.filter(listed_by_id=agent_filter)

    agents = BusinessEmployee.objects.filter(business=biz, is_active=True)
    return render(request, 'property_listings/property_list.html', {
        'biz': biz, 'access_level': level, 'properties': props,
        'type_filter': type_filter, 'status_filter': status_filter,
        'property_types': Property.PROPERTY_TYPES, 'statuses': Property.STATUS,
        'agents': agents, 'agent_filter': agent_filter,
    })


@login_required
def property_add(request, slug):
    biz, emp, level = _pl_check(slug, request.user, min_level=2)
    if not level:
        return redirect('property_listings:property_list', slug=slug)

    agents = BusinessEmployee.objects.filter(business=biz, is_active=True)

    if request.method == 'POST':
        agent_id = request.POST.get('listed_by_id')
        agent = BusinessEmployee.objects.filter(pk=agent_id, business=biz).first() if agent_id else emp
        prop = Property.objects.create(
            business=biz,
            title=request.POST['title'],
            property_type=request.POST.get('property_type', 'house'),
            listing_type=request.POST.get('listing_type', 'sale'),
            status=request.POST.get('status', 'active'),
            address=request.POST['address'],
            city=request.POST.get('city', ''),
            region=request.POST.get('region', ''),
            country=request.POST.get('country', ''),
            bedrooms=request.POST.get('bedrooms') or None,
            bathrooms=request.POST.get('bathrooms') or None,
            area_sqft=request.POST.get('area_sqft') or None,
            price=request.POST.get('price') or None,
            currency=request.POST.get('currency', 'USD'),
            rent_per_month=request.POST.get('rent_per_month') or None,
            mls_number=request.POST.get('mls_number', ''),
            listing_url=request.POST.get('listing_url', ''),
            virtual_tour_url=request.POST.get('virtual_tour_url', ''),
            description=request.POST.get('description', ''),
            features=request.POST.get('features', ''),
            listed_by=agent,
            listing_date=request.POST.get('listing_date') or None,
        )
        messages.success(request, f'Property "{prop.title}" listed.')
        return redirect('property_listings:property_detail', slug=slug, property_id=prop.pk)

    return render(request, 'property_listings/property_form.html', {
        'biz': biz, 'access_level': level, 'agents': agents,
        'property_types': Property.PROPERTY_TYPES, 'statuses': Property.STATUS,
        'listing_types': Property.LISTING_TYPES,
    })


@login_required
def property_detail(request, slug, property_id):
    biz, emp, level = _pl_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    prop = get_object_or_404(Property, pk=property_id, business=biz)
    agents = BusinessEmployee.objects.filter(business=biz, is_active=True)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'add_showing':
            agent_id = request.POST.get('agent_id')
            agent = BusinessEmployee.objects.filter(pk=agent_id, business=biz).first() if agent_id else emp
            PropertyShowing.objects.create(
                property=prop,
                contact_name=request.POST['contact_name'],
                contact_phone=request.POST.get('contact_phone', ''),
                contact_email=request.POST.get('contact_email', ''),
                scheduled_at=request.POST['scheduled_at'],
                agent=agent,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Showing scheduled.')
        elif action == 'update_showing':
            showing = get_object_or_404(PropertyShowing, pk=request.POST.get('showing_id'), property=prop)
            showing.status = request.POST.get('status', showing.status)
            showing.feedback = request.POST.get('feedback', showing.feedback)
            showing.save(update_fields=['status', 'feedback'])
        elif action == 'update_status' and level >= 3:
            new_status = request.POST.get('status')
            if new_status in dict(Property.STATUS):
                prop.status = new_status
                prop.save(update_fields=['status'])
                messages.success(request, f'Status updated to {prop.get_status_display()}.')
        return redirect('property_listings:property_detail', slug=slug, property_id=property_id)

    showings = prop.showings.all()
    return render(request, 'property_listings/property_detail.html', {
        'biz': biz, 'access_level': level, 'prop': prop,
        'showings': showings, 'agents': agents,
        'statuses': Property.STATUS, 'showing_statuses': PropertyShowing.SHOWING_STATUS,
    })
