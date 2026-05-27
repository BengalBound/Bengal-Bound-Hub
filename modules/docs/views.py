from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from hub.views import _get_business_for_user
from hub.access import require_employee
from .models import HubDoc, DocShare


@require_employee
def doc_list(request, slug):
    from hub.views import _get_business_for_user
    biz = _get_business_for_user(slug, request.user)
    my_docs = HubDoc.objects.filter(business=biz, created_by=request.user)
    shared_ids = DocShare.objects.filter(shared_with=request.user).values_list('doc_id', flat=True)
    shared_docs = HubDoc.objects.filter(pk__in=shared_ids).exclude(created_by=request.user)
    templates = HubDoc.objects.filter(business=biz, is_template=True)
    return render(request, 'docs/list.html', {
        'biz': biz, 'my_docs': my_docs, 'shared_docs': shared_docs, 'templates': templates,
        'current_business': biz,
    })


@require_employee
def doc_create(request, slug):
    biz = _get_business_for_user(slug, request.user)
    doc = HubDoc.objects.create(business=biz, created_by=request.user)
    return redirect('docs:doc_edit', slug=slug, pk=doc.pk)


@require_employee
def doc_edit(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    doc = get_object_or_404(HubDoc, pk=pk, business=biz)
    # Check edit access
    if doc.created_by != request.user:
        share = DocShare.objects.filter(doc=doc, shared_with=request.user, access_level='edit').first()
        if not share:
            messages.error(request, 'You only have view access to this document.')
            return redirect('docs:doc_view', slug=slug, pk=pk)

    if request.method == 'POST':
        doc.title = request.POST.get('title', doc.title).strip() or 'Untitled Document'
        doc.content = request.POST.get('content', '')
        doc.is_template = request.POST.get('is_template') == '1'
        doc.last_edited_by = request.user
        doc.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'title': doc.title})
        messages.success(request, 'Document saved.')
        return redirect('docs:doc_edit', slug=slug, pk=pk)

    return render(request, 'docs/editor.html', {'biz': biz, 'doc': doc, 'current_business': biz})


@require_employee
def doc_view(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    doc = get_object_or_404(HubDoc, pk=pk, business=biz)
    return render(request, 'docs/view.html', {'biz': biz, 'doc': doc, 'current_business': biz})


@require_employee
def doc_delete(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    doc = get_object_or_404(HubDoc, pk=pk, business=biz, created_by=request.user)
    doc.delete()
    messages.success(request, 'Document deleted.')
    return redirect('docs:doc_list', slug=slug)


@require_employee
def doc_share(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    doc = get_object_or_404(HubDoc, pk=pk, business=biz, created_by=request.user)
    if request.method == 'POST':
        from accounts.models import User
        email = request.POST.get('email', '').strip()
        access = request.POST.get('access', 'view')
        try:
            target = User.objects.get(email=email)
            DocShare.objects.update_or_create(
                doc=doc, shared_with=target,
                defaults={'access_level': access, 'shared_by': request.user}
            )
            doc.is_shared = True
            doc.save(update_fields=['is_shared'])
            messages.success(request, f'Shared with {email}.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return redirect('docs:doc_edit', slug=slug, pk=pk)
