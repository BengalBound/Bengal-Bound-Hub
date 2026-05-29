from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils.text import slugify

from hub.views import _get_business_for_user
from .models import CustomDashboard, DashboardWidget, DashboardSharedUser


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    my_dashboards = CustomDashboard.objects.filter(business=biz, created_by=request.user)
    shared = CustomDashboard.objects.filter(
        business=biz, shared_users__user=request.user
    ).distinct()
    return render(request, 'dashboard_pro/index.html', {
        'biz': biz,
        'my_dashboards': my_dashboards,
        'shared': shared,
        'total_dashboards': my_dashboards.count(),
        'recent_dashboards': my_dashboards[:6],
    })


@login_required(login_url='/accounts/login/')
def dashboard_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            name = request.POST.get('name', '').strip()
            db_slug = slugify(name) or 'dashboard'
            CustomDashboard.objects.create(
                business=biz,
                name=name,
                slug=db_slug,
                description=request.POST.get('description', ''),
                icon=request.POST.get('icon', 'bi-grid').strip(),
                color=request.POST.get('color', '#3b82f6').strip(),
                is_default=request.POST.get('is_default') == 'on',
                created_by=request.user,
            )
            messages.success(request, f'Dashboard "{name}" created.')
        elif action == 'delete':
            CustomDashboard.objects.filter(pk=request.POST.get('dashboard_id'), business=biz, created_by=request.user).delete()
            messages.success(request, 'Dashboard deleted.')
        return redirect('dashboard_pro:dashboard_list', slug=slug)
    dashboards = CustomDashboard.objects.filter(business=biz).select_related('created_by')
    return render(request, 'dashboard_pro/dashboard_list.html', {'biz': biz, 'dashboards': dashboards})


@login_required(login_url='/accounts/login/')
def dashboard_view(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    dashboard = get_object_or_404(CustomDashboard, pk=pk, business=biz)
    can_edit = (dashboard.created_by == request.user or
                dashboard.shared_users.filter(user=request.user, access_level='edit').exists())
    widgets = dashboard.widgets.filter(is_visible=True).order_by('position_y', 'position_x')
    if request.method == 'POST' and can_edit:
        action = request.POST.get('action')
        if action == 'add_widget':
            DashboardWidget.objects.create(
                dashboard=dashboard,
                widget_type=request.POST.get('widget_type', 'stat_card'),
                title=request.POST.get('title', '').strip(),
                subtitle=request.POST.get('subtitle', '').strip(),
                width=request.POST.get('width', 4) or 4,
                height=request.POST.get('height', 2) or 2,
            )
            messages.success(request, 'Widget added.')
        elif action == 'remove_widget':
            DashboardWidget.objects.filter(pk=request.POST.get('widget_id'), dashboard=dashboard).delete()
            messages.success(request, 'Widget removed.')
        elif action == 'share':
            from accounts.models import User
            user_email = request.POST.get('user_email', '').strip()
            try:
                share_user = User.objects.get(email=user_email)
                DashboardSharedUser.objects.get_or_create(
                    dashboard=dashboard, user=share_user,
                    defaults={'access_level': request.POST.get('access_level', 'view')}
                )
                messages.success(request, f'Dashboard shared with {user_email}.')
            except User.DoesNotExist:
                messages.error(request, f'User {user_email} not found.')
        return redirect('dashboard_pro:dashboard_view', slug=slug, pk=pk)
    return render(request, 'dashboard_pro/dashboard_view.html', {
        'biz': biz, 'dashboard': dashboard, 'widgets': widgets, 'can_edit': can_edit,
    })
