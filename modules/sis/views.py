from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models as dj_models
from django.utils import timezone
from hub.models import BusinessInstance, BusinessEmployee
from .models import Student, ParentGuardian, SubjectGrade, StudentAttendance


def _sis_check(slug, user, min_level=1):
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
def sis_dashboard(request, slug):
    biz, emp, level = _sis_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    students = Student.objects.filter(business=biz)
    now = timezone.now()
    stats = {
        'total': students.count(),
        'active': students.filter(status='active').count(),
        'graduated': students.filter(status='graduated').count(),
        'new_this_month': students.filter(enrolled_date__year=now.year, enrolled_date__month=now.month).count(),
    }
    classes = students.values_list('class_group', flat=True).distinct().order_by('class_group')
    recent = students.order_by('-created_at')[:8]

    return render(request, 'sis/dashboard.html', {
        'biz': biz, 'access_level': level,
        'stats': stats, 'classes': classes, 'recent_students': recent,
    })


@login_required
def student_list(request, slug):
    biz, emp, level = _sis_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    students = Student.objects.filter(business=biz)
    status_filter = request.GET.get('status', '')
    class_filter = request.GET.get('class_group', '')
    q = request.GET.get('q', '')

    if status_filter:
        students = students.filter(status=status_filter)
    if class_filter:
        students = students.filter(class_group=class_filter)
    if q:
        students = students.filter(
            dj_models.Q(first_name__icontains=q) |
            dj_models.Q(last_name__icontains=q) |
            dj_models.Q(enrollment_number__icontains=q)
        )

    all_classes = Student.objects.filter(business=biz).values_list('class_group', flat=True).distinct().order_by('class_group')

    return render(request, 'sis/student_list.html', {
        'biz': biz, 'access_level': level, 'students': students,
        'status_filter': status_filter, 'class_filter': class_filter,
        'q': q, 'all_classes': all_classes, 'statuses': Student.STATUS,
    })


@login_required
def student_add(request, slug):
    biz, emp, level = _sis_check(slug, request.user, min_level=3)
    if not level:
        return redirect('sis:student_list', slug=slug)

    if request.method == 'POST':
        student = Student.objects.create(
            business=biz,
            enrollment_number=request.POST.get('enrollment_number', ''),
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
            date_of_birth=request.POST.get('date_of_birth') or None,
            gender=request.POST.get('gender', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            class_group=request.POST.get('class_group', ''),
            section=request.POST.get('section', ''),
            enrolled_date=request.POST.get('enrolled_date') or None,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f"Student {student.full_name} enrolled.")
        return redirect('sis:student_detail', slug=slug, student_id=student.pk)

    return render(request, 'sis/student_form.html', {
        'biz': biz, 'access_level': level,
        'genders': Student.GENDER,
    })


@login_required
def student_detail(request, slug, student_id):
    biz, emp, level = _sis_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    student = get_object_or_404(Student, pk=student_id, business=biz)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')

        if action == 'add_grade':
            SubjectGrade.objects.create(
                student=student,
                subject=request.POST.get('subject', ''),
                period=request.POST.get('period', ''),
                score=request.POST.get('score') or None,
                max_score=request.POST.get('max_score') or 100,
                grade_letter=request.POST.get('grade_letter', ''),
                recorded_by=emp,
                notes=request.POST.get('grade_notes', ''),
            )
            messages.success(request, 'Grade recorded.')

        elif action == 'mark_attendance':
            StudentAttendance.objects.update_or_create(
                student=student,
                date=request.POST.get('att_date', ''),
                subject=request.POST.get('att_subject', ''),
                defaults={
                    'status': request.POST.get('att_status', 'present'),
                    'notes': request.POST.get('att_notes', ''),
                    'recorded_by': emp,
                },
            )
            messages.success(request, 'Attendance marked.')

        elif action == 'add_parent':
            ParentGuardian.objects.create(
                student=student,
                name=request.POST.get('parent_name', ''),
                relationship=request.POST.get('relationship', 'guardian'),
                email=request.POST.get('parent_email', ''),
                phone=request.POST.get('parent_phone', ''),
                is_primary=request.POST.get('is_primary') == '1',
            )
            messages.success(request, 'Parent / guardian added.')

        elif action == 'update_status':
            student.status = request.POST.get('status', student.status)
            if request.POST.get('class_group'):
                student.class_group = request.POST.get('class_group', '')
            if request.POST.get('section'):
                student.section = request.POST.get('section', '')
            student.save()
            messages.success(request, 'Student record updated.')

        return redirect('sis:student_detail', slug=slug, student_id=student_id)

    grades = student.grades.all()
    attendance = student.attendance_records.all()[:30]
    parents = student.parents.all()

    present_count = student.attendance_records.filter(status='present').count()
    total_att = student.attendance_records.count()
    attendance_pct = round((present_count / total_att) * 100, 1) if total_att else None

    return render(request, 'sis/student_detail.html', {
        'biz': biz, 'access_level': level, 'student': student,
        'grades': grades, 'attendance': attendance, 'parents': parents,
        'attendance_pct': attendance_pct,
        'statuses': Student.STATUS,
        'att_statuses': StudentAttendance.STATUS,
        'relationships': ParentGuardian.RELATIONSHIP,
    })
