from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hub.models import BusinessInstance, BusinessEmployee
from .models import ProgressReport, ReportSubjectLine, ParentMessage, Announcement


def _pp_check(slug, user, min_level=1):
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
def portal_home(request, slug):
    biz, emp, level = _pp_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    reports = ProgressReport.objects.filter(business=biz)
    messages_qs = ParentMessage.objects.filter(business=biz)
    announcements = Announcement.objects.filter(business=biz)

    stats = {
        'reports': reports.count(),
        'shared': reports.filter(is_shared=True).count(),
        'messages': messages_qs.count(),
        'announcements': announcements.count(),
    }
    recent_reports = reports.order_by('-report_date')[:5]
    recent_msgs = messages_qs.order_by('-sent_at')[:5]
    pinned_announcements = announcements.filter(is_pinned=True)[:3]

    return render(request, 'parent_portal/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats,
        'recent_reports': recent_reports, 'recent_msgs': recent_msgs,
        'pinned_announcements': pinned_announcements,
    })


@login_required
def report_list(request, slug):
    biz, emp, level = _pp_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'create_report':
            report = ProgressReport.objects.create(
                business=biz,
                student_name=request.POST.get('student_name', ''),
                student_ref=request.POST.get('student_ref', ''),
                class_group=request.POST.get('class_group', ''),
                period=request.POST.get('period', ''),
                report_date=request.POST.get('report_date', ''),
                overall_grade=request.POST.get('overall_grade', ''),
                gpa=request.POST.get('gpa') or None,
                attendance_pct=request.POST.get('attendance_pct') or None,
                teacher_comments=request.POST.get('teacher_comments', ''),
                generated_by=emp,
            )
            messages.success(request, f"Report created for {report.student_name}.")
            return redirect('parent_portal:report_detail', slug=slug, report_id=report.pk)
        return redirect('parent_portal:report_list', slug=slug)

    reports = ProgressReport.objects.filter(business=biz)
    period_filter = request.GET.get('period', '')
    if period_filter:
        reports = reports.filter(period=period_filter)

    periods = ProgressReport.objects.filter(business=biz).values_list('period', flat=True).distinct()

    return render(request, 'parent_portal/report_list.html', {
        'biz': biz, 'access_level': level, 'reports': reports,
        'period_filter': period_filter, 'periods': periods,
    })


@login_required
def report_detail(request, slug, report_id):
    biz, emp, level = _pp_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    report = get_object_or_404(ProgressReport, pk=report_id, business=biz)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_subject':
            ReportSubjectLine.objects.create(
                report=report,
                subject=request.POST.get('subject', ''),
                score=request.POST.get('score', ''),
                grade=request.POST.get('grade', ''),
                teacher=request.POST.get('teacher', ''),
                comment=request.POST.get('comment', ''),
            )
            messages.success(request, 'Subject line added.')
        elif action == 'share':
            report.generate_share_link()
            messages.success(request, 'Share link generated.')
        elif action == 'unshare':
            report.is_shared = False
            report.share_token = ''
            report.save(update_fields=['is_shared', 'share_token'])
            messages.success(request, 'Report is now private.')
        return redirect('parent_portal:report_detail', slug=slug, report_id=report_id)

    subject_lines = report.subject_lines.all()
    share_url = None
    if report.is_shared and report.share_token:
        share_url = request.build_absolute_uri(f"/portal/report/{report.share_token}/")

    return render(request, 'parent_portal/report_detail.html', {
        'biz': biz, 'access_level': level, 'report': report,
        'subject_lines': subject_lines, 'share_url': share_url,
    })


def report_public(request, token):
    report = get_object_or_404(ProgressReport, share_token=token, is_shared=True)
    subject_lines = report.subject_lines.all()
    return render(request, 'parent_portal/report_public.html', {
        'report': report, 'subject_lines': subject_lines,
    })


@login_required
def message_list(request, slug):
    biz, emp, level = _pp_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        ParentMessage.objects.create(
            business=biz,
            from_employee=emp,
            parent_name=request.POST.get('parent_name', ''),
            parent_email=request.POST.get('parent_email', ''),
            student_name=request.POST.get('student_name', ''),
            subject=request.POST.get('subject', ''),
            body=request.POST.get('body', ''),
            is_urgent='is_urgent' in request.POST,
        )
        messages.success(request, 'Message logged.')
        return redirect('parent_portal:message_list', slug=slug)

    msgs = ParentMessage.objects.filter(business=biz)
    return render(request, 'parent_portal/message_list.html', {
        'biz': biz, 'access_level': level, 'msgs': msgs,
    })


@login_required
def announcement_list(request, slug):
    biz, emp, level = _pp_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'post':
            Announcement.objects.create(
                business=biz,
                title=request.POST.get('title', ''),
                body=request.POST.get('body', ''),
                audience=request.POST.get('audience', 'all'),
                class_group=request.POST.get('class_group', ''),
                posted_by=emp,
                is_pinned='is_pinned' in request.POST,
            )
            messages.success(request, 'Announcement posted.')
        elif action == 'delete':
            Announcement.objects.filter(pk=request.POST.get('ann_id'), business=biz).delete()
            messages.success(request, 'Announcement deleted.')
        return redirect('parent_portal:announcement_list', slug=slug)

    announcements = Announcement.objects.filter(business=biz)
    return render(request, 'parent_portal/announcement_list.html', {
        'biz': biz, 'access_level': level, 'announcements': announcements,
        'audiences': Announcement.AUDIENCE,
    })
