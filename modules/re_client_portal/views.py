from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from hub.models import BusinessInstance, BusinessEmployee
from .models import ClientPortalAccess, PortalDocument


def _rcp_check(slug, user, min_level=1):
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
def portal_home(request, slug):
    biz, emp, level = _rcp_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    accesses = ClientPortalAccess.objects.filter(business=biz)
    total_docs = PortalDocument.objects.filter(access__business=biz).count()

    stats = {
        'clients': accesses.count(),
        'active': accesses.filter(is_active=True).count(),
        'total_docs': total_docs,
        'signed': PortalDocument.objects.filter(access__business=biz, is_signed=True).count(),
    }

    return render(request, 're_client_portal/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats,
        'accesses': accesses[:10],
    })


@login_required
def client_list(request, slug):
    biz, emp, level = _rcp_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'create_access':
            ClientPortalAccess.objects.create(
                business=biz,
                client_name=request.POST['client_name'],
                client_email=request.POST['client_email'],
                deal_reference=request.POST.get('deal_reference', ''),
                expires_at=request.POST.get('expires_at') or None,
                welcome_message=request.POST.get('welcome_message', ''),
                created_by=emp,
            )
            messages.success(request, 'Client portal access created.')
        elif action == 'toggle_access':
            access = get_object_or_404(ClientPortalAccess, pk=request.POST.get('access_id'), business=biz)
            access.is_active = not access.is_active
            access.save(update_fields=['is_active'])
        return redirect('re_client_portal:client_list', slug=slug)

    accesses = ClientPortalAccess.objects.filter(business=biz)
    return render(request, 're_client_portal/client_list.html', {
        'biz': biz, 'access_level': level, 'accesses': accesses,
    })


@login_required
def client_detail(request, slug, access_id):
    biz, emp, level = _rcp_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    access = get_object_or_404(ClientPortalAccess, pk=access_id, business=biz)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'add_document':
            PortalDocument.objects.create(
                access=access,
                document_name=request.POST['document_name'],
                doc_type=request.POST.get('doc_type', 'other'),
                source='agent',
                file_url=request.POST.get('file_url', ''),
                notes=request.POST.get('notes', ''),
                is_signed='is_signed' in request.POST,
            )
            messages.success(request, 'Document added to client portal.')
        elif action == 'delete_doc':
            PortalDocument.objects.filter(pk=request.POST.get('doc_id'), access=access).delete()
        elif action == 'mark_signed':
            doc = get_object_or_404(PortalDocument, pk=request.POST.get('doc_id'), access=access)
            doc.is_signed = True
            doc.save(update_fields=['is_signed'])
        return redirect('re_client_portal:client_detail', slug=slug, access_id=access_id)

    docs = access.documents.all()
    portal_url = request.build_absolute_uri(f"/hub/re-portal/view/{access.token}/")
    return render(request, 're_client_portal/client_detail.html', {
        'biz': biz, 'access_level': level, 'access': access,
        'docs': docs, 'portal_url': portal_url,
        'doc_types': PortalDocument.DOC_TYPES,
    })


def portal_view(request, token):
    access = get_object_or_404(ClientPortalAccess, token=token, is_active=True)
    if access.expires_at and access.expires_at < timezone.now().date():
        return render(request, 're_client_portal/portal_expired.html', {'access': access})
    docs = access.documents.all()
    return render(request, 're_client_portal/portal_view.html', {
        'access': access, 'docs': docs,
    })
