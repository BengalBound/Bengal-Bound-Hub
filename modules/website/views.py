from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils.text import slugify

from hub.views import _get_business_for_user
from .models import WebsiteProject, WebPage, WebsiteAsset


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    projects = WebsiteProject.objects.filter(business=biz)
    stats = {
        'total': projects.count(),
        'live': projects.filter(status='live').count(),
        'in_progress': projects.filter(status='in_progress').count(),
        'pages': WebPage.objects.filter(project__business=biz).count(),
    }
    return render(request, 'website/index.html', {
        'biz': biz, 'projects': projects, 'stats': stats,
    })


@login_required(login_url='/accounts/login/')
def project_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            WebsiteProject.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                website_type=request.POST.get('website_type', 'business'),
                domain=request.POST.get('domain', '').strip(),
                description=request.POST.get('description', ''),
                created_by=request.user,
                assigned_to=request.user,
            )
            messages.success(request, 'Website project created.')
        elif action == 'delete':
            WebsiteProject.objects.filter(pk=request.POST.get('project_id'), business=biz).delete()
            messages.success(request, 'Project deleted.')
        return redirect('website:project_list', slug=slug)
    projects = WebsiteProject.objects.filter(business=biz).select_related('created_by', 'assigned_to')
    return render(request, 'website/project_list.html', {'biz': biz, 'projects': projects})


@login_required(login_url='/accounts/login/')
def project_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    project = get_object_or_404(WebsiteProject, pk=pk, business=biz)
    pages = project.pages.order_by('nav_order', 'title')
    assets = project.assets.order_by('-created_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            project.name = request.POST.get('name', project.name).strip() or project.name
            project.status = request.POST.get('status', project.status)
            project.domain = request.POST.get('domain', project.domain).strip()
            project.live_url = request.POST.get('live_url', project.live_url).strip()
            project.staging_url = request.POST.get('staging_url', project.staging_url).strip()
            project.seo_title = request.POST.get('seo_title', project.seo_title).strip()
            project.seo_description = request.POST.get('seo_description', project.seo_description)
            project.save()
            messages.success(request, 'Project updated.')
        elif action == 'add_page':
            title = request.POST.get('title', '').strip()
            page_slug = slugify(title)
            base = page_slug
            i = 1
            while WebPage.objects.filter(project=project, slug=page_slug).exists():
                page_slug = f"{base}-{i}"
                i += 1
            WebPage.objects.create(
                project=project,
                title=title,
                slug=page_slug,
                content=request.POST.get('content', ''),
                is_homepage=request.POST.get('is_homepage') == 'on',
                in_navigation=request.POST.get('in_navigation') == 'on',
                nav_order=pages.count(),
                created_by=request.user,
            )
            messages.success(request, f'Page "{title}" added.')
        elif action == 'delete_page':
            WebPage.objects.filter(pk=request.POST.get('page_id'), project=project).delete()
            messages.success(request, 'Page deleted.')
        elif action == 'upload_asset':
            f = request.FILES.get('file')
            if f:
                WebsiteAsset.objects.create(
                    project=project,
                    name=f.name,
                    asset_type=request.POST.get('asset_type', 'image'),
                    file=f,
                    alt_text=request.POST.get('alt_text', '').strip(),
                    file_size=f.size,
                    uploaded_by=request.user,
                )
                messages.success(request, f'"{f.name}" uploaded.')
        return redirect('website:project_detail', slug=slug, pk=pk)
    return render(request, 'website/project_detail.html', {
        'biz': biz, 'project': project, 'pages': pages, 'assets': assets,
    })
