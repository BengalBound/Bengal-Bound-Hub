from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages

from hub.views import _get_business_for_user
from .models import Campaign, EmailList, Subscriber, EmailTemplate


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    campaigns = Campaign.objects.filter(business=biz)
    recent = campaigns.order_by('-created_at')[:5]
    return render(request, 'email_marketing/index.html', {
        'biz': biz,
        'total_campaigns': campaigns.count(),
        'sent_campaigns': campaigns.filter(status='sent').count(),
        'total_subscribers': Subscriber.objects.filter(email_list__business=biz, is_subscribed=True).count(),
        'total_lists': EmailList.objects.filter(business=biz, is_active=True).count(),
        'recent_campaigns': recent,
    })


@login_required(login_url='/accounts/login/')
def campaign_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    campaigns = Campaign.objects.filter(business=biz).order_by('-created_at')
    return render(request, 'email_marketing/campaign_list.html', {'biz': biz, 'campaigns': campaigns})


@login_required(login_url='/accounts/login/')
def campaign_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    lists = EmailList.objects.filter(business=biz, is_active=True)
    templates = EmailTemplate.objects.filter(business=biz)
    if request.method == 'POST':
        c = Campaign.objects.create(
            business=biz, name=request.POST.get('name', '').strip(),
            subject=request.POST.get('subject', '').strip(),
            from_name=request.POST.get('from_name', '').strip(),
            from_email=request.POST.get('from_email', '').strip(),
            html_content=request.POST.get('html_content', ''),
            email_list_id=request.POST.get('email_list') or None,
            created_by=request.user,
        )
        messages.success(request, f'Campaign "{c.name}" created.')
        return redirect('email_marketing:campaign_detail', slug=slug, pk=c.pk)
    return render(request, 'email_marketing/campaign_form.html', {'biz': biz, 'lists': lists, 'templates': templates})


@login_required(login_url='/accounts/login/')
def campaign_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    campaign = get_object_or_404(Campaign, pk=pk, business=biz)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            campaign.delete()
            messages.success(request, 'Campaign deleted.')
            return redirect('email_marketing:campaign_list', slug=slug)
    return render(request, 'email_marketing/campaign_detail.html', {'biz': biz, 'campaign': campaign})


@login_required(login_url='/accounts/login/')
def email_lists(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            EmailList.objects.create(business=biz, name=request.POST.get('name', '').strip(), description=request.POST.get('description', ''))
            messages.success(request, 'List created.')
        elif action == 'delete':
            EmailList.objects.filter(pk=request.POST.get('list_id'), business=biz).delete()
            messages.success(request, 'List deleted.')
        return redirect('email_marketing:email_lists', slug=slug)
    all_lists = EmailList.objects.filter(business=biz)
    return render(request, 'email_marketing/email_lists.html', {'biz': biz, 'email_lists': all_lists})


@login_required(login_url='/accounts/login/')
def subscribers(request, slug, list_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    email_list = get_object_or_404(EmailList, pk=list_id, business=biz)
    subs = email_list.subscribers.order_by('-subscribed_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            email = request.POST.get('email', '').strip()
            if email:
                Subscriber.objects.get_or_create(email_list=email_list, email=email, defaults={'first_name': request.POST.get('first_name', ''), 'last_name': request.POST.get('last_name', '')})
                messages.success(request, f'{email} added.')
        return redirect('email_marketing:subscribers', slug=slug, list_id=list_id)
    return render(request, 'email_marketing/subscribers.html', {'biz': biz, 'email_list': email_list, 'subscribers': subs})
