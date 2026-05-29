from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from hub.views import _get_business_for_user
from hub.access import require_employee
from .models import DriveFolder, DriveFile


@require_employee
def drive_home(request, slug):
    biz = _get_business_for_user(slug, request.user)
    root_folders = DriveFolder.objects.filter(business=biz, parent__isnull=True)
    root_files = DriveFile.objects.filter(business=biz, folder__isnull=True, is_trashed=False)
    total_bytes = DriveFile.objects.filter(business=biz, is_trashed=False).aggregate(
        s=__import__('django.db.models', fromlist=['Sum']).Sum('size_bytes')
    )['s'] or 0
    return render(request, 'cloud_drive/home.html', {
        'biz': biz, 'root_folders': root_folders, 'root_files': root_files,
        'total_mb': round(total_bytes / (1024 * 1024), 2), 'current_business': biz,
    })


@require_employee
def drive_folder(request, slug, folder_id):
    biz = _get_business_for_user(slug, request.user)
    folder = get_object_or_404(DriveFolder, pk=folder_id, business=biz)
    sub_folders = DriveFolder.objects.filter(parent=folder)
    files = DriveFile.objects.filter(folder=folder, is_trashed=False)
    return render(request, 'cloud_drive/folder.html', {
        'biz': biz, 'folder': folder, 'sub_folders': sub_folders, 'files': files, 'current_business': biz,
    })


@require_employee
def drive_upload(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if request.method == 'POST':
        folder_id = request.POST.get('folder_id')
        folder = DriveFolder.objects.filter(pk=folder_id, business=biz).first() if folder_id else None
        uploaded_files = request.FILES.getlist('files')
        for f in uploaded_files:
            DriveFile.objects.create(
                business=biz,
                folder=folder,
                name=f.name,
                file=f,
                size_bytes=f.size,
                mime_type=f.content_type or '',
                uploaded_by=request.user,
            )
            # Update business storage
            biz.storage_used_mb += f.size / (1024 * 1024)
        biz.save(update_fields=['storage_used_mb'])
        messages.success(request, f'{len(uploaded_files)} file(s) uploaded.')
        if folder:
            return redirect('cloud_drive:drive_folder', slug=slug, folder_id=folder.pk)
    return redirect('cloud_drive:drive_home', slug=slug)


@require_employee
def drive_new_folder(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if request.method == 'POST':
        name = request.POST.get('name', 'New Folder').strip()
        parent_id = request.POST.get('parent_id')
        parent = DriveFolder.objects.filter(pk=parent_id, business=biz).first() if parent_id else None
        DriveFolder.objects.create(business=biz, name=name, parent=parent, created_by=request.user)
        messages.success(request, f'Folder "{name}" created.')
        if parent:
            return redirect('cloud_drive:drive_folder', slug=slug, folder_id=parent.pk)
    return redirect('cloud_drive:drive_home', slug=slug)


@require_employee
def drive_file_delete(request, slug, file_id):
    biz = _get_business_for_user(slug, request.user)
    f = get_object_or_404(DriveFile, pk=file_id, business=biz)
    biz.storage_used_mb = max(0, biz.storage_used_mb - f.size_bytes / (1024 * 1024))
    biz.save(update_fields=['storage_used_mb'])
    f.delete()
    messages.success(request, 'File deleted.')
    return redirect('cloud_drive:drive_home', slug=slug)


@require_employee
def drive_file_star(request, slug, file_id):
    biz = _get_business_for_user(slug, request.user)
    f = get_object_or_404(DriveFile, pk=file_id, business=biz)
    f.is_starred = not f.is_starred
    f.save(update_fields=['is_starred'])
    return redirect(request.META.get('HTTP_REFERER', '/'))
