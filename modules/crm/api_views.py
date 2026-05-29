"""
modules/crm/api_views.py
Lightweight JSON API for the CRM module.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.http import Http404

from .models import Contact, Deal
from hub.models import BusinessInstance, BusinessEmployee


def _get_biz(request, slug):
    try:
        biz = BusinessInstance.objects.get(slug=slug, is_active=True)
    except BusinessInstance.DoesNotExist:
        raise Http404
    if biz.owner == request.user:
        return biz
    emp = BusinessEmployee.objects.filter(business=biz, user=request.user, is_active=True).first()
    if emp and emp.can_access_module('crm'):
        return biz
    raise Http404


def _contact_to_dict(c):
    return {
        'id': c.id,
        'type': c.contact_type,
        'name': c.full_name,
        'email': c.email,
        'phone': c.phone,
        'company': c.company_name,
        'city': c.city,
        'country': c.country,
        'tags': c.tags,
        'created_at': c.created_at.isoformat(),
    }


def _deal_to_dict(d):
    return {
        'id': d.id,
        'title': d.title,
        'value': float(d.value) if d.value else 0,
        'currency': d.currency,
        'stage': d.stage.name if d.stage else None,
        'pipeline': d.stage.pipeline.name if d.stage and d.stage.pipeline else None,
        'contact': d.contact.full_name if d.contact else None,
        'probability': d.probability,
        'expected_close': d.expected_close.isoformat() if d.expected_close else None,
        'status': d.status,
    }


@login_required
@require_GET
def api_contacts(request, slug):
    """GET /hub/<slug>/crm/api/contacts/"""
    try:
        biz = _get_biz(request, slug)
    except Http404:
        return JsonResponse({'error': 'Not found'}, status=404)

    search = request.GET.get('q', '')
    qs = Contact.objects.filter(business=biz)
    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(company_name__icontains=search) |
            Q(email__icontains=search)
        )

    limit = min(int(request.GET.get('limit', 50)), 200)
    qs = qs.order_by('-created_at')[:limit]
    return JsonResponse({'count': len(qs), 'results': [_contact_to_dict(c) for c in qs]})


@login_required
@require_GET
def api_contact_detail(request, slug, pk):
    """GET /hub/<slug>/crm/api/contacts/<pk>/"""
    try:
        biz = _get_biz(request, slug)
    except Http404:
        return JsonResponse({'error': 'Not found'}, status=404)

    try:
        c = Contact.objects.get(pk=pk, business=biz)
    except Contact.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    return JsonResponse(_contact_to_dict(c))


@login_required
@require_GET
def api_deals(request, slug):
    """GET /hub/<slug>/crm/api/deals/"""
    try:
        biz = _get_biz(request, slug)
    except Http404:
        return JsonResponse({'error': 'Not found'}, status=404)

    status_filter = request.GET.get('status', '')
    qs = Deal.objects.filter(stage__pipeline__business=biz).select_related('stage__pipeline', 'contact')
    if status_filter:
        qs = qs.filter(status=status_filter)
    qs = qs.order_by('-created_at')[:100]
    return JsonResponse({'count': len(qs), 'results': [_deal_to_dict(d) for d in qs]})


@login_required
@require_GET
def api_deal_detail(request, slug, pk):
    """GET /hub/<slug>/crm/api/deals/<pk>/"""
    try:
        biz = _get_biz(request, slug)
    except Http404:
        return JsonResponse({'error': 'Not found'}, status=404)

    try:
        d = Deal.objects.get(pk=pk, stage__pipeline__business=biz)
    except Deal.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    return JsonResponse(_deal_to_dict(d))
