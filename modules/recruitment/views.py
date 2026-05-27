from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q

from hub.views import _get_business_for_user
from .models import JobPosting, Applicant, Application, Interview


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    recent_jobs = JobPosting.objects.filter(business=biz).order_by('-created_at')[:5]
    recent_apps = Application.objects.filter(job__business=biz).select_related('applicant', 'job').order_by('-applied_at')[:8]
    return render(request, 'recruitment/index.html', {
        'biz': biz,
        'open_jobs': JobPosting.objects.filter(business=biz, status='open').count(),
        'total_applications': Application.objects.filter(job__business=biz).count(),
        'interviews_scheduled': Application.objects.filter(job__business=biz, stage='interview').count(),
        'offers_made': Application.objects.filter(job__business=biz, stage='hired').count(),
        'recent_jobs': recent_jobs,
        'recent_apps': recent_apps,
    })


@login_required(login_url='/accounts/login/')
def job_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status = request.GET.get('status', '')
    qs = JobPosting.objects.filter(business=biz)
    if status:
        qs = qs.filter(status=status)
    return render(request, 'recruitment/job_list.html', {'biz': biz, 'jobs': qs, 'status_filter': status})


@login_required(login_url='/accounts/login/')
def job_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        job = JobPosting.objects.create(
            business=biz, title=request.POST.get('title', '').strip(),
            department=request.POST.get('department', ''), location=request.POST.get('location', ''),
            job_type=request.POST.get('job_type', 'full_time'),
            description=request.POST.get('description', ''),
            requirements=request.POST.get('requirements', ''),
            salary_min=request.POST.get('salary_min') or None,
            salary_max=request.POST.get('salary_max') or None,
            deadline=request.POST.get('deadline') or None,
            openings=int(request.POST.get('openings', 1)),
            status='open' if 'publish' in request.POST else 'draft',
            created_by=request.user, hiring_manager=request.user,
        )
        messages.success(request, f'Job posting "{job.title}" created.')
        return redirect('recruitment:job_detail', slug=slug, pk=job.pk)
    return render(request, 'recruitment/job_form.html', {'biz': biz})


@login_required(login_url='/accounts/login/')
def job_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    job = get_object_or_404(JobPosting, pk=pk, business=biz)
    applications = job.applications.select_related('applicant').order_by('-applied_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            job.status = request.POST.get('status', job.status)
            job.save(update_fields=['status'])
            messages.success(request, f'Job status updated to {job.status}.')
        elif action == 'delete':
            job.delete()
            messages.success(request, 'Job posting deleted.')
            return redirect('recruitment:job_list', slug=slug)
        return redirect('recruitment:job_detail', slug=slug, pk=pk)
    return render(request, 'recruitment/job_detail.html', {'biz': biz, 'job': job, 'applications': applications})


@login_required(login_url='/accounts/login/')
def application_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    stage = request.GET.get('stage', '')
    qs = Application.objects.filter(job__business=biz).select_related('applicant', 'job')
    if stage:
        qs = qs.filter(stage=stage)
    return render(request, 'recruitment/application_list.html', {'biz': biz, 'applications': qs, 'stage_filter': stage})


@login_required(login_url='/accounts/login/')
def application_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    app = get_object_or_404(Application, pk=pk, job__business=biz)
    interviews = app.interviews.order_by('-scheduled_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'move_stage':
            app.stage = request.POST.get('stage', app.stage)
            app.notes = request.POST.get('notes', app.notes)
            app.save(update_fields=['stage', 'notes'])
            messages.success(request, f'Application moved to {app.stage}.')
        elif action == 'add_interview':
            Interview.objects.create(
                application=app, interview_type=request.POST.get('interview_type', 'video'),
                scheduled_at=request.POST.get('scheduled_at'),
                duration_minutes=int(request.POST.get('duration', 60)),
                location=request.POST.get('location', ''),
            )
            messages.success(request, 'Interview scheduled.')
        return redirect('recruitment:application_detail', slug=slug, pk=pk)
    return render(request, 'recruitment/application_detail.html', {'biz': biz, 'application': app, 'interviews': interviews})
