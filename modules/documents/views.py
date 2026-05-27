from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q

from hub.views import _get_business_for_user
from .models import Document, DocumentFolder, DocumentShare


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    folders = DocumentFolder.objects.filter(business=biz, parent=None)
    recent_docs = Document.objects.filter(business=biz, is_archived=False).order_by('-created_at')[:12]
    stats = {
        'total_docs': Document.objects.filter(business=biz).count(),
        'total_folders': DocumentFolder.objects.filter(business=biz).count(),
        'shared_with_me': DocumentShare.objects.filter(shared_with=request.user).count(),
    }
    return render(request, 'documents/index.html', {'biz': biz, 'folders': folders, 'recent_docs': recent_docs, 'stats': stats})


@login_required(login_url='/accounts/login/')
def folder_view(request, slug, folder_id=None):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    folder = get_object_or_404(DocumentFolder, pk=folder_id, business=biz) if folder_id else None
    subfolders = DocumentFolder.objects.filter(business=biz, parent=folder)
    docs = Document.objects.filter(business=biz, folder=folder, is_archived=False)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_folder':
            DocumentFolder.objects.create(business=biz, name=request.POST.get('name', '').strip(), parent=folder, created_by=request.user)
            messages.success(request, 'Folder created.')
        elif action == 'upload':
            f = request.FILES.get('file')
            if f:
                doc = Document.objects.create(
                    business=biz, folder=folder, name=f.name, file=f,
                    file_size=f.size, mime_type=f.content_type or '',
                    uploaded_by=request.user,
                )
                messages.success(request, f'"{doc.name}" uploaded.')
        elif action == 'delete_folder':
            DocumentFolder.objects.filter(pk=request.POST.get('folder_id'), business=biz).delete()
            messages.success(request, 'Folder deleted.')
        return redirect('documents:folder_view', slug=slug, folder_id=folder.pk) if folder else redirect('documents:index', slug=slug)
    return render(request, 'documents/folder_view.html', {'biz': biz, 'folder': folder, 'subfolders': subfolders, 'docs': docs})


@login_required(login_url='/accounts/login/')
def document_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    doc = get_object_or_404(Document, pk=pk, business=biz)
    shares = doc.shares.select_related('shared_with')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'rename':
            doc.name = request.POST.get('name', doc.name).strip() or doc.name
            doc.description = request.POST.get('description', doc.description)
            doc.tags = request.POST.get('tags', doc.tags)
            doc.save()
            messages.success(request, 'Document updated.')
        elif action == 'archive':
            doc.is_archived = True
            doc.save(update_fields=['is_archived'])
            messages.info(request, 'Document archived.')
            return redirect('documents:index', slug=slug)
        elif action == 'delete':
            doc.delete()
            messages.success(request, 'Document deleted.')
            return redirect('documents:index', slug=slug)
        return redirect('documents:document_detail', slug=slug, pk=pk)
    return render(request, 'documents/document_detail.html', {'biz': biz, 'doc': doc, 'shares': shares})
