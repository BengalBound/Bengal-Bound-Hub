from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import Course, CourseModule, Enrollment

try:
    from modules.hr.models import Employee
except ImportError:
    Employee = None


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    courses = Course.objects.filter(business=biz)
    recent_courses = courses.order_by('-created_at')[:8]
    return render(request, 'training/index.html', {
        'biz': biz,
        'total_courses': courses.count(),
        'active_courses': courses.filter(status='published').count(),
        'total_enrolled': Enrollment.objects.filter(course__business=biz).count(),
        'completions': Enrollment.objects.filter(course__business=biz, status='completed').count(),
        'recent_courses': recent_courses,
    })


@login_required(login_url='/accounts/login/')
def course_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status_filter = request.GET.get('status', '')
    qs = Course.objects.filter(business=biz).order_by('title')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'training/course_list.html', {
        'biz': biz, 'courses': qs, 'status_filter': status_filter,
    })


@login_required(login_url='/accounts/login/')
def course_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        course = Course.objects.create(
            business=biz,
            title=request.POST.get('title', '').strip(),
            description=request.POST.get('description', ''),
            level=request.POST.get('level', 'beginner'),
            status=request.POST.get('status', 'draft'),
            duration_hours=request.POST.get('duration_hours', 0) or 0,
            category=request.POST.get('category', '').strip(),
            is_mandatory=request.POST.get('is_mandatory') == 'on',
            created_by=request.user,
        )
        messages.success(request, f'Course "{course.title}" created.')
        return redirect('training:course_detail', slug=slug, pk=course.pk)
    return render(request, 'training/course_form.html', {'biz': biz})


@login_required(login_url='/accounts/login/')
def course_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    course = get_object_or_404(Course, pk=pk, business=biz)
    modules = course.modules.order_by('position')
    enrollments = course.enrollments.select_related('employee')
    employees = Employee.objects.filter(business=biz, status='active') if Employee else []
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_module':
            pos = modules.count()
            CourseModule.objects.create(
                course=course,
                title=request.POST.get('title', '').strip(),
                module_type=request.POST.get('module_type', 'article'),
                content=request.POST.get('content', ''),
                duration_minutes=request.POST.get('duration_minutes', 0) or 0,
                position=pos,
            )
            messages.success(request, 'Module added.')
        elif action == 'enroll':
            emp = get_object_or_404(Employee, pk=request.POST.get('employee'), business=biz) if Employee else None
            if emp:
                Enrollment.objects.get_or_create(course=course, employee=emp)
                messages.success(request, f'{emp} enrolled.')
        elif action == 'update_enrollment':
            enr = get_object_or_404(Enrollment, pk=request.POST.get('enrollment_id'), course=course)
            enr.status = request.POST.get('status', enr.status)
            enr.progress_pct = request.POST.get('progress_pct', enr.progress_pct) or enr.progress_pct
            if enr.status == 'completed' and not enr.completed_at:
                enr.completed_at = timezone.now()
            enr.save()
            messages.success(request, 'Enrollment updated.')
        elif action == 'update_course':
            course.title = request.POST.get('title', course.title).strip() or course.title
            course.status = request.POST.get('status', course.status)
            course.description = request.POST.get('description', course.description)
            course.save()
            messages.success(request, 'Course updated.')
        elif action == 'delete':
            course.delete()
            messages.success(request, 'Course deleted.')
            return redirect('training:course_list', slug=slug)
        return redirect('training:course_detail', slug=slug, pk=pk)
    return render(request, 'training/course_detail.html', {
        'biz': biz, 'course': course, 'modules': modules,
        'enrollments': enrollments, 'employees': employees,
    })
