from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hub.models import BusinessInstance, BusinessEmployee
from .models import Course, CourseModule, Lesson, LearnerEnrollment, LessonProgress


def _lms_check(slug, user, min_level=1):
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
def lms_home(request, slug):
    biz, emp, level = _lms_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    courses = Course.objects.filter(business=biz)
    stats = {
        'courses': courses.count(),
        'published': courses.filter(status='published').count(),
        'enrollments': LearnerEnrollment.objects.filter(course__business=biz).count(),
        'completed': LearnerEnrollment.objects.filter(course__business=biz, status='completed').count(),
    }
    my_enrollments = LearnerEnrollment.objects.filter(learner=emp).select_related('course').order_by('-enrolled_at')[:5]
    recent_courses = courses.filter(status='published').order_by('-created_at')[:6]

    return render(request, 'lms/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats,
        'my_enrollments': my_enrollments, 'recent_courses': recent_courses,
    })


@login_required
def course_list(request, slug):
    biz, emp, level = _lms_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    courses = Course.objects.filter(business=biz)
    status_filter = request.GET.get('status', '')
    if status_filter:
        courses = courses.filter(status=status_filter)

    enrolled_ids = LearnerEnrollment.objects.filter(learner=emp).values_list('course_id', flat=True)

    return render(request, 'lms/course_list.html', {
        'biz': biz, 'access_level': level, 'courses': courses,
        'status_filter': status_filter, 'statuses': Course.STATUS,
        'enrolled_ids': list(enrolled_ids),
    })


@login_required
def course_create(request, slug):
    biz, emp, level = _lms_check(slug, request.user, min_level=3)
    if not level:
        return redirect('lms:course_list', slug=slug)

    if request.method == 'POST':
        course = Course.objects.create(
            business=biz,
            title=request.POST['title'],
            code=request.POST.get('code', ''),
            description=request.POST.get('description', ''),
            instructor_id=request.POST.get('instructor_id') or None,
            category=request.POST.get('category', ''),
            level=request.POST.get('level', 'all'),
            audience=request.POST.get('audience', 'students'),
            duration_hours=request.POST.get('duration_hours') or None,
            is_self_paced='is_self_paced' in request.POST,
            pass_score_pct=request.POST.get('pass_score_pct', 70),
            certificate_on_completion='certificate_on_completion' in request.POST,
        )
        messages.success(request, f"Course '{course.title}' created.")
        return redirect('lms:course_detail', slug=slug, course_id=course.pk)

    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    return render(request, 'lms/course_form.html', {
        'biz': biz, 'access_level': level,
        'employees': employees, 'levels': Course.LEVEL, 'audiences': Course.AUDIENCE,
    })


@login_required
def course_detail(request, slug, course_id):
    biz, emp, level = _lms_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    course = get_object_or_404(Course, pk=course_id, business=biz)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')

        if action == 'add_module':
            CourseModule.objects.create(
                course=course,
                title=request.POST['module_title'],
                description=request.POST.get('module_description', ''),
                order=course.modules.count() + 1,
            )
            messages.success(request, 'Module added.')

        elif action == 'add_lesson':
            mod = get_object_or_404(CourseModule, pk=request.POST['module_id'], course=course)
            Lesson.objects.create(
                module=mod,
                title=request.POST['lesson_title'],
                content_type=request.POST.get('content_type', 'text'),
                content_text=request.POST.get('content_text', ''),
                content_url=request.POST.get('content_url', ''),
                duration_minutes=request.POST.get('duration_minutes') or None,
                order=mod.lessons.count() + 1,
                is_preview='is_preview' in request.POST,
            )
            messages.success(request, 'Lesson added.')

        elif action == 'publish':
            course.status = 'published' if course.status != 'published' else 'draft'
            course.save()
            messages.success(request, f"Course is now {course.get_status_display()}.")

        elif action == 'enroll':
            learner_id = request.POST.get('learner_id')
            learner = get_object_or_404(BusinessEmployee, pk=learner_id, business=biz)
            _, created = LearnerEnrollment.objects.get_or_create(course=course, learner=learner)
            if created:
                messages.success(request, f"{learner.user.get_full_name()} enrolled.")
            else:
                messages.info(request, 'Already enrolled.')

        return redirect('lms:course_detail', slug=slug, course_id=course_id)

    modules = course.modules.prefetch_related('lessons').all()
    enrollments = course.enrollments.select_related('learner__user').all()
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    my_enrollment = LearnerEnrollment.objects.filter(course=course, learner=emp).first()

    return render(request, 'lms/course_detail.html', {
        'biz': biz, 'access_level': level, 'course': course,
        'modules': modules, 'enrollments': enrollments,
        'employees': employees, 'my_enrollment': my_enrollment,
        'content_types': Lesson.CONTENT_TYPE,
    })
