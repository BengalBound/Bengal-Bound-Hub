from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from hub.models import BusinessInstance, BusinessEmployee
from .models import Quiz, Question, QuestionChoice, QuizAttempt, AttemptAnswer


def _ass_check(slug, user, min_level=1):
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
def assessments_home(request, slug):
    biz, emp, level = _ass_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    quizzes = Quiz.objects.filter(business=biz)
    stats = {
        'total': quizzes.count(),
        'published': quizzes.filter(status='published').count(),
        'attempts': QuizAttempt.objects.filter(quiz__business=biz).count(),
        'passed': QuizAttempt.objects.filter(quiz__business=biz, is_passed=True).count(),
    }
    my_attempts = QuizAttempt.objects.filter(taken_by=emp).select_related('quiz').order_by('-started_at')[:5]

    return render(request, 'assessments/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats,
        'quizzes': quizzes.filter(status='published')[:8],
        'my_attempts': my_attempts,
    })


@login_required
def quiz_list(request, slug):
    biz, emp, level = _ass_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    quizzes = Quiz.objects.filter(business=biz)
    status_filter = request.GET.get('status', '')
    if status_filter:
        quizzes = quizzes.filter(status=status_filter)

    return render(request, 'assessments/quiz_list.html', {
        'biz': biz, 'access_level': level, 'quizzes': quizzes,
        'status_filter': status_filter, 'statuses': Quiz.STATUS,
    })


@login_required
def quiz_create(request, slug):
    biz, emp, level = _ass_check(slug, request.user, min_level=3)
    if not level:
        return redirect('assessments:quiz_list', slug=slug)

    if request.method == 'POST':
        quiz = Quiz.objects.create(
            business=biz,
            title=request.POST.get('title', ''),
            description=request.POST.get('description', ''),
            course_ref=request.POST.get('course_ref', ''),
            time_limit_minutes=request.POST.get('time_limit_minutes') or None,
            pass_score_pct=request.POST.get('pass_score_pct', 70),
            allow_retakes='allow_retakes' in request.POST,
            max_attempts=request.POST.get('max_attempts', 3),
            shuffle_questions='shuffle_questions' in request.POST,
            show_answers_after='show_answers_after' in request.POST,
            created_by=emp,
        )
        messages.success(request, f"Quiz '{quiz.title}' created.")
        return redirect('assessments:quiz_detail', slug=slug, quiz_id=quiz.pk)

    return render(request, 'assessments/quiz_form.html', {'biz': biz, 'access_level': level})


@login_required
def quiz_detail(request, slug, quiz_id):
    biz, emp, level = _ass_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    quiz = get_object_or_404(Quiz, pk=quiz_id, business=biz)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')

        if action == 'add_question':
            q = Question.objects.create(
                quiz=quiz,
                question_text=request.POST.get('question_text', ''),
                question_type=request.POST.get('question_type', 'mc'),
                points=request.POST.get('points', 1),
                order=quiz.questions.count() + 1,
                explanation=request.POST.get('explanation', ''),
            )
            # Add choices for mc/tf
            for i in range(1, 6):
                ct = request.POST.get(f'choice_{i}', '').strip()
                if ct:
                    QuestionChoice.objects.create(
                        question=q,
                        choice_text=ct,
                        is_correct=request.POST.get(f'correct_{i}') == '1',
                        order=i,
                    )
            messages.success(request, 'Question added.')

        elif action == 'delete_question':
            Question.objects.filter(pk=request.POST.get('question_id'), quiz=quiz).delete()
            messages.success(request, 'Question deleted.')

        elif action == 'publish':
            quiz.status = 'published' if quiz.status != 'published' else 'draft'
            quiz.save()
            messages.success(request, f"Quiz is now {quiz.get_status_display()}.")

        return redirect('assessments:quiz_detail', slug=slug, quiz_id=quiz_id)

    questions = quiz.questions.prefetch_related('choices').all()
    attempts = quiz.attempts.select_related('taken_by__user').order_by('-started_at')[:20]
    my_attempts = quiz.attempts.filter(taken_by=emp).order_by('-started_at')

    return render(request, 'assessments/quiz_detail.html', {
        'biz': biz, 'access_level': level, 'quiz': quiz,
        'questions': questions, 'attempts': attempts, 'my_attempts': my_attempts,
        'question_types': Question.TYPE,
    })


@login_required
def take_quiz(request, slug, quiz_id):
    biz, emp, level = _ass_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    quiz = get_object_or_404(Quiz, pk=quiz_id, business=biz, status='published')

    # Check attempt limit
    attempt_count = QuizAttempt.objects.filter(quiz=quiz, taken_by=emp).count()
    if not quiz.allow_retakes and attempt_count > 0:
        messages.warning(request, 'You have already completed this quiz.')
        return redirect('assessments:quiz_detail', slug=slug, quiz_id=quiz_id)
    if quiz.allow_retakes and attempt_count >= quiz.max_attempts:
        messages.warning(request, f'Maximum attempts ({quiz.max_attempts}) reached.')
        return redirect('assessments:quiz_detail', slug=slug, quiz_id=quiz_id)

    if request.method == 'POST':
        attempt = QuizAttempt.objects.create(
            quiz=quiz, taken_by=emp, attempt_number=attempt_count + 1
        )
        questions = quiz.questions.prefetch_related('choices').all()
        total_pts = 0
        earned_pts = 0

        for q in questions:
            total_pts += float(q.points)
            ans_text = request.POST.get(f'q_{q.pk}', '')
            chosen_id = request.POST.get(f'q_{q.pk}_choice')
            chosen = None
            is_correct = None
            score_earned = 0

            if q.question_type in ('mc', 'tf') and chosen_id:
                try:
                    chosen = QuestionChoice.objects.get(pk=chosen_id, question=q)
                    is_correct = chosen.is_correct
                    if is_correct:
                        score_earned = float(q.points)
                        earned_pts += score_earned
                except QuestionChoice.DoesNotExist:
                    pass

            AttemptAnswer.objects.create(
                attempt=attempt, question=q,
                answer_text=ans_text, selected_choice=chosen,
                is_correct=is_correct, score_earned=score_earned,
            )

        score_pct = round((earned_pts / total_pts) * 100, 2) if total_pts > 0 else 0
        attempt.score_pct = score_pct
        attempt.is_passed = score_pct >= quiz.pass_score_pct
        attempt.submitted_at = timezone.now()
        attempt.save()

        messages.success(request, f"Quiz submitted! Score: {score_pct}% — {'Passed' if attempt.is_passed else 'Not passed'}.")
        return redirect('assessments:quiz_result', slug=slug, attempt_id=attempt.pk)

    questions = list(quiz.questions.prefetch_related('choices').all())
    if quiz.shuffle_questions:
        import random
        random.shuffle(questions)

    return render(request, 'assessments/take_quiz.html', {
        'biz': biz, 'access_level': level, 'quiz': quiz, 'questions': questions,
    })


@login_required
def quiz_result(request, slug, attempt_id):
    biz, emp, level = _ass_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, quiz__business=biz)
    if attempt.taken_by != emp and level < 3:
        return redirect('assessments:assessments_home', slug=slug)

    answers = attempt.answers.select_related('question', 'selected_choice').all()

    return render(request, 'assessments/quiz_result.html', {
        'biz': biz, 'access_level': level, 'attempt': attempt, 'answers': answers,
    })
