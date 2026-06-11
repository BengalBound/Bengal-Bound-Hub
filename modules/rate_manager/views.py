from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hub.models import BusinessInstance, BusinessEmployee
from .models import Season, RoomRateBase, YieldRule, RateRestriction, SpecialOffer


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
def rm_home(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    stats = {
        'seasons': Season.objects.filter(business=biz).count(),
        'base_rates': RoomRateBase.objects.filter(business=biz).count(),
        'active_rules': YieldRule.objects.filter(business=biz, is_active=True).count(),
        'active_offers': SpecialOffer.objects.filter(business=biz, is_active=True).count(),
    }
    recent_seasons = Season.objects.filter(business=biz)[:5]
    recent_offers = SpecialOffer.objects.filter(business=biz, is_active=True)[:5]

    return render(request, 'rate_manager/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats,
        'recent_seasons': recent_seasons, 'recent_offers': recent_offers,
    })


@login_required
def seasons(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_season':
            season = Season.objects.create(
                business=biz,
                name=request.POST.get('name', ''),
                season_type=request.POST.get('season_type', 'shoulder'),
                start_date=request.POST.get('start_date', ''),
                end_date=request.POST.get('end_date', ''),
                rate_multiplier=request.POST.get('rate_multiplier') or 1.00,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, f'Season "{season.name}" added.')
        return redirect('rate_manager:seasons', slug=slug)

    all_seasons = Season.objects.filter(business=biz)
    return render(request, 'rate_manager/seasons.html', {
        'biz': biz, 'access_level': level, 'seasons': all_seasons,
        'season_types': Season.SEASON_TYPES,
    })


@login_required
def base_rates(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_rate':
            rate = RoomRateBase.objects.create(
                business=biz,
                room_type_name=request.POST.get('room_type_name', ''),
                base_rate=request.POST.get('base_rate', ''),
                currency=request.POST.get('currency', 'USD'),
                effective_from=request.POST.get('effective_from', ''),
                effective_to=request.POST.get('effective_to') or None,
            )
            messages.success(request, f'Base rate for "{rate.room_type_name}" added.')
        elif action == 'delete_rate':
            rate = get_object_or_404(RoomRateBase, pk=request.POST.get('rate_id'), business=biz)
            name = rate.room_type_name
            rate.delete()
            messages.success(request, f'Base rate for "{name}" deleted.')
        return redirect('rate_manager:base_rates', slug=slug)

    rates = RoomRateBase.objects.filter(business=biz)
    return render(request, 'rate_manager/base_rates.html', {
        'biz': biz, 'access_level': level, 'rates': rates,
    })


@login_required
def yield_rules(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_rule':
            rule = YieldRule.objects.create(
                business=biz,
                name=request.POST.get('name', ''),
                rule_type=request.POST.get('rule_type', ''),
                threshold_value=request.POST.get('threshold_value', ''),
                adjustment_type=request.POST.get('adjustment_type', 'percent'),
                adjustment_value=request.POST.get('adjustment_value', ''),
                priority=request.POST.get('priority') or 0,
            )
            messages.success(request, f'Yield rule "{rule.name}" added.')
        elif action == 'toggle_rule':
            rule = get_object_or_404(YieldRule, pk=request.POST.get('rule_id'), business=biz)
            rule.is_active = not rule.is_active
            rule.save(update_fields=['is_active'])
            state = 'activated' if rule.is_active else 'deactivated'
            messages.success(request, f'Rule "{rule.name}" {state}.')
        elif action == 'add_restriction':
            restriction = RateRestriction.objects.create(
                business=biz,
                room_type_name=request.POST.get('room_type_name', ''),
                restriction_type=request.POST.get('restriction_type', ''),
                value=request.POST.get('value') or 1,
                start_date=request.POST.get('start_date', ''),
                end_date=request.POST.get('end_date', ''),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, f'Restriction "{restriction.get_restriction_type_display()}" added.')
        return redirect('rate_manager:yield_rules', slug=slug)

    rules = YieldRule.objects.filter(business=biz)
    restrictions = RateRestriction.objects.filter(business=biz)
    return render(request, 'rate_manager/yield_rules.html', {
        'biz': biz, 'access_level': level, 'rules': rules, 'restrictions': restrictions,
        'rule_types': YieldRule.RULE_TYPES, 'adjustment_types': YieldRule.ADJUSTMENT_TYPES,
        'restriction_types': RateRestriction.RESTRICTION_TYPES,
    })


@login_required
def special_offers(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_offer':
            offer = SpecialOffer.objects.create(
                business=biz,
                name=request.POST.get('name', ''),
                offer_type=request.POST.get('offer_type', ''),
                discount_type=request.POST.get('discount_type', 'percent'),
                discount_value=request.POST.get('discount_value', ''),
                valid_from=request.POST.get('valid_from', ''),
                valid_to=request.POST.get('valid_to', ''),
                promo_code=request.POST.get('promo_code', ''),
                description=request.POST.get('description', ''),
            )
            messages.success(request, f'Special offer "{offer.name}" added.')
        elif action == 'toggle_offer':
            offer = get_object_or_404(SpecialOffer, pk=request.POST.get('offer_id'), business=biz)
            offer.is_active = not offer.is_active
            offer.save(update_fields=['is_active'])
            state = 'activated' if offer.is_active else 'deactivated'
            messages.success(request, f'Offer "{offer.name}" {state}.')
        return redirect('rate_manager:special_offers', slug=slug)

    offers = SpecialOffer.objects.filter(business=biz)
    return render(request, 'rate_manager/special_offers.html', {
        'biz': biz, 'access_level': level, 'offers': offers,
        'offer_types': SpecialOffer.OFFER_TYPES, 'discount_types': SpecialOffer.DISCOUNT_TYPES,
    })
