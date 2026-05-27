from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from hub.views import _get_business_for_user
from hub.access import get_access_level
from .models import CADProject, CADFile


def _cadcam_check(slug, user, min_level=3):
    biz = _get_business_for_user(slug, user)
    if not biz:
        return None, HttpResponseForbidden()
    if get_access_level(biz, user) < min_level:
        return None, HttpResponseForbidden()
    return biz, None


@login_required(login_url='/accounts/login/')
def cadcam_home(request, slug):
    biz, err = _cadcam_check(slug, request.user)
    if err:
        return err

    projects = CADProject.objects.filter(business=biz).select_related('owner')
    return render(request, 'cadcam/home.html', {
        'biz': biz,
        'projects': projects,
        'tools': CADProject.TOOLS,
        'statuses': CADProject.STATUS,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def cadcam_project_create(request, slug):
    biz, err = _cadcam_check(slug, request.user, min_level=4)
    if err:
        return err

    if request.method == 'POST':
        from hub.models import BusinessEmployee
        owner_id = request.POST.get('owner_id', '')
        CADProject.objects.create(
            business=biz,
            name=request.POST.get('name', '').strip(),
            description=request.POST.get('description', '').strip(),
            tool=request.POST.get('tool', 'other'),
            owner_id=int(owner_id) if owner_id else None,
        )
        messages.success(request, "CAD/CAM project created.")
        return redirect('cadcam:home', slug=slug)

    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    return render(request, 'cadcam/project_form.html', {
        'biz': biz,
        'employees': employees,
        'tools': CADProject.TOOLS,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def cadcam_project_detail(request, slug, project_id):
    biz, err = _cadcam_check(slug, request.user)
    if err:
        return err

    project = get_object_or_404(CADProject, pk=project_id, business=biz)

    if request.method == 'POST':
        file_obj = request.FILES.get('file')
        CADFile.objects.create(
            project=project,
            filename=request.POST.get('filename', '').strip() or (file_obj.name if file_obj else 'Untitled'),
            file=file_obj,
            format=request.POST.get('format', 'other'),
            version=request.POST.get('version', '1.0'),
            description=request.POST.get('description', '').strip(),
            uploaded_by=request.user,
        )
        messages.success(request, "File uploaded.")
        return redirect('cadcam:project_detail', slug=slug, project_id=project_id)

    files = project.files.all()
    return render(request, 'cadcam/project_detail.html', {
        'biz': biz,
        'project': project,
        'files': files,
        'formats': CADFile.FORMATS,
        'is_owner': biz.owner == request.user,
    })
