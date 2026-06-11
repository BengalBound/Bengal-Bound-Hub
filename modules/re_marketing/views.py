from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hub.models import BusinessInstance, BusinessEmployee
from .models import ListingFlyer, DripCampaign, DripMessage, SocialPost


def _rem_check(slug, user, min_level=1):
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
def marketing_home(request, slug):
    biz, emp, level = _rem_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    stats = {
        'flyers': ListingFlyer.objects.filter(business=biz).count(),
        'campaigns': DripCampaign.objects.filter(business=biz).count(),
        'active_campaigns': DripCampaign.objects.filter(business=biz, status='active').count(),
        'social_posts': SocialPost.objects.filter(business=biz).count(),
    }
    recent_flyers = ListingFlyer.objects.filter(business=biz)[:5]
    recent_posts = SocialPost.objects.filter(business=biz)[:5]
    campaigns = DripCampaign.objects.filter(business=biz)[:5]

    return render(request, 're_marketing/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats,
        'recent_flyers': recent_flyers, 'recent_posts': recent_posts, 'campaigns': campaigns,
    })


@login_required
def flyer_list(request, slug):
    biz, emp, level = _rem_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        ListingFlyer.objects.create(
            business=biz,
            property_address=request.POST.get('property_address', ''),
            template=request.POST.get('template', 'standard'),
            headline=request.POST.get('headline', ''),
            tagline=request.POST.get('tagline', ''),
            bedrooms=request.POST.get('bedrooms') or None,
            bathrooms=request.POST.get('bathrooms') or None,
            price=request.POST.get('price', ''),
            open_house_date=request.POST.get('open_house_date', ''),
            agent_name=request.POST.get('agent_name', ''),
            agent_phone=request.POST.get('agent_phone', ''),
            agent_email=request.POST.get('agent_email', ''),
            property_url=request.POST.get('property_url', ''),
            virtual_tour_url=request.POST.get('virtual_tour_url', ''),
            notes=request.POST.get('notes', ''),
            created_by=emp,
        )
        messages.success(request, 'Flyer created.')
        return redirect('re_marketing:flyer_list', slug=slug)

    flyers = ListingFlyer.objects.filter(business=biz)
    return render(request, 're_marketing/flyer_list.html', {
        'biz': biz, 'access_level': level, 'flyers': flyers,
        'templates': ListingFlyer.TEMPLATES,
    })


@login_required
def campaign_list(request, slug):
    biz, emp, level = _rem_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'create_campaign':
            DripCampaign.objects.create(
                business=biz,
                name=request.POST.get('name', ''),
                target_audience=request.POST.get('target_audience', 'all'),
                description=request.POST.get('description', ''),
                created_by=emp,
            )
            messages.success(request, 'Campaign created.')
        elif action == 'add_message':
            campaign = get_object_or_404(DripCampaign, pk=request.POST.get('campaign_id'), business=biz)
            DripMessage.objects.create(
                campaign=campaign,
                subject=request.POST.get('subject', ''),
                body=request.POST.get('body', ''),
                delay_days=request.POST.get('delay_days', 0),
                message_type=request.POST.get('message_type', 'email'),
            )
            messages.success(request, 'Message added to campaign.')
        elif action == 'toggle_status':
            campaign = get_object_or_404(DripCampaign, pk=request.POST.get('campaign_id'), business=biz)
            campaign.status = 'active' if campaign.status != 'active' else 'paused'
            campaign.save(update_fields=['status'])
        return redirect('re_marketing:campaign_list', slug=slug)

    campaigns = DripCampaign.objects.filter(business=biz).prefetch_related('messages')
    return render(request, 're_marketing/campaign_list.html', {
        'biz': biz, 'access_level': level, 'campaigns': campaigns,
        'audiences': DripCampaign.AUDIENCE, 'msg_types': DripMessage.MSG_TYPES,
    })


@login_required
def social_posts(request, slug):
    biz, emp, level = _rem_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'create_post':
            SocialPost.objects.create(
                business=biz,
                post_type=request.POST.get('post_type', 'just_listed'),
                property_address=request.POST.get('property_address', ''),
                caption=request.POST.get('caption', ''),
                platform=request.POST.get('platform', 'both'),
                scheduled_for=request.POST.get('scheduled_for') or None,
                created_by=emp,
            )
            messages.success(request, 'Post queued.')
        elif action == 'mark_posted':
            post = get_object_or_404(SocialPost, pk=request.POST.get('post_id'), business=biz)
            post.status = 'posted'
            post.save(update_fields=['status'])
        elif action == 'delete_post':
            SocialPost.objects.filter(pk=request.POST.get('post_id'), business=biz).delete()
        return redirect('re_marketing:social_posts', slug=slug)

    posts = SocialPost.objects.filter(business=biz)
    return render(request, 're_marketing/social_posts.html', {
        'biz': biz, 'access_level': level, 'posts': posts,
        'post_types': SocialPost.POST_TYPES, 'platforms': SocialPost.PLATFORMS,
        'post_statuses': SocialPost.POST_STATUS,
    })
