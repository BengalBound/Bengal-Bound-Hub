from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum

from hub.views import _get_business_for_user
from .models import Project, Milestone, Task, TimeEntry, ProjectComment


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    projects = Project.objects.filter(business=biz)
    today = timezone.now().date()
    recent = projects.order_by('-updated_at')[:6]
    return render(request, 'projects/index.html', {
        'biz': biz,
        'total_projects': projects.count(),
        'active_projects': projects.filter(status='active').count(),
        'completed_projects': projects.filter(status='completed').count(),
        'total_tasks': Task.objects.filter(project__business=biz).count(),
        'overdue_tasks': Task.objects.filter(project__business=biz, due_date__lt=today).exclude(status='done').count(),
        'recent_projects': recent,
    })


@login_required(login_url='/accounts/login/')
def project_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status_filter = request.GET.get('status', '')
    qs = Project.objects.filter(business=biz).order_by('-updated_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'projects/project_list.html', {
        'biz': biz, 'projects': qs, 'status_filter': status_filter,
    })


@login_required(login_url='/accounts/login/')
def project_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        project = Project.objects.create(
            business=biz,
            name=request.POST.get('name', '').strip(),
            description=request.POST.get('description', ''),
            status=request.POST.get('status', 'planning'),
            priority=request.POST.get('priority', 'medium'),
            start_date=request.POST.get('start_date') or None,
            end_date=request.POST.get('end_date') or None,
            budget=request.POST.get('budget') or None,
            client_name=request.POST.get('client_name', '').strip(),
            client_email=request.POST.get('client_email', '').strip(),
            created_by=request.user,
        )
        messages.success(request, f'Project "{project.name}" created.')
        return redirect('projects:project_detail', slug=slug, pk=project.pk)
    return render(request, 'projects/project_form.html', {'biz': biz})


@login_required(login_url='/accounts/login/')
def project_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    project = get_object_or_404(Project, pk=pk, business=biz)
    milestones = project.milestones.order_by('due_date')
    tasks = project.tasks.select_related('assignee', 'milestone').order_by('status', 'due_date')
    comments = project.comments.select_related('user').order_by('created_at')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_task':
            Task.objects.create(
                project=project,
                milestone_id=request.POST.get('milestone') or None,
                title=request.POST.get('title', '').strip(),
                description=request.POST.get('description', ''),
                status=request.POST.get('status', 'todo'),
                priority=request.POST.get('priority', 'medium'),
                assignee_id=request.POST.get('assignee') or None,
                due_date=request.POST.get('due_date') or None,
                estimated_hours=request.POST.get('estimated_hours') or 0,
                created_by=request.user,
            )
            messages.success(request, 'Task added.')

        elif action == 'add_milestone':
            Milestone.objects.create(
                project=project,
                title=request.POST.get('title', '').strip(),
                description=request.POST.get('description', ''),
                due_date=request.POST.get('due_date'),
            )
            messages.success(request, 'Milestone added.')

        elif action == 'complete_milestone':
            m = get_object_or_404(Milestone, pk=request.POST.get('milestone_id'), project=project)
            m.is_completed = True
            m.completed_at = timezone.now()
            m.save(update_fields=['is_completed', 'completed_at'])
            messages.success(request, f'Milestone "{m.title}" marked complete.')

        elif action == 'update_status':
            project.status = request.POST.get('status', project.status)
            project.save(update_fields=['status'])
            messages.success(request, 'Project status updated.')

        elif action == 'add_comment':
            content = request.POST.get('content', '').strip()
            if content:
                ProjectComment.objects.create(project=project, user=request.user, content=content)
                messages.success(request, 'Comment added.')

        elif action == 'delete':
            project.delete()
            messages.success(request, 'Project deleted.')
            return redirect('projects:project_list', slug=slug)

        return redirect('projects:project_detail', slug=slug, pk=pk)

    return render(request, 'projects/project_detail.html', {
        'biz': biz, 'project': project,
        'milestones': milestones, 'tasks': tasks, 'comments': comments,
    })


@login_required(login_url='/accounts/login/')
def task_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    task = get_object_or_404(Task, pk=pk, project__business=biz)
    time_entries = task.time_entries.select_related('user').order_by('-date')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_task':
            task.title = request.POST.get('title', task.title).strip() or task.title
            task.status = request.POST.get('status', task.status)
            task.priority = request.POST.get('priority', task.priority)
            task.description = request.POST.get('description', task.description)
            task.due_date = request.POST.get('due_date') or task.due_date
            task.estimated_hours = request.POST.get('estimated_hours') or task.estimated_hours
            task.save()
            messages.success(request, 'Task updated.')

        elif action == 'log_time':
            hours = request.POST.get('hours') or 0
            TimeEntry.objects.create(
                task=task,
                user=request.user,
                description=request.POST.get('description', '').strip(),
                hours=hours,
                date=request.POST.get('date') or timezone.now().date(),
            )
            task.actual_hours = task.time_entries.aggregate(s=Sum('hours'))['s'] or 0
            task.save(update_fields=['actual_hours'])
            messages.success(request, f'{hours}h logged.')

        elif action == 'delete_entry':
            TimeEntry.objects.filter(pk=request.POST.get('entry_id'), task=task).delete()
            task.actual_hours = task.time_entries.aggregate(s=Sum('hours'))['s'] or 0
            task.save(update_fields=['actual_hours'])
            messages.success(request, 'Time entry removed.')

        elif action == 'delete_task':
            project_pk = task.project.pk
            task.delete()
            messages.success(request, 'Task deleted.')
            return redirect('projects:project_detail', slug=slug, pk=project_pk)

        return redirect('projects:task_detail', slug=slug, pk=pk)

    return render(request, 'projects/task_detail.html', {
        'biz': biz, 'task': task, 'time_entries': time_entries,
    })


@login_required(login_url='/accounts/login/')
def milestones(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    today = timezone.now().date()
    status_filter = request.GET.get('status', '')
    qs = Milestone.objects.filter(project__business=biz).select_related('project').order_by('due_date')
    if status_filter == 'pending':
        qs = qs.filter(is_completed=False)
    elif status_filter == 'completed':
        qs = qs.filter(is_completed=True)
    elif status_filter == 'overdue':
        qs = qs.filter(is_completed=False, due_date__lt=today)
    return render(request, 'projects/milestones.html', {
        'biz': biz, 'milestones': qs, 'status_filter': status_filter,
    })
