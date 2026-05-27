from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class Quiz(models.Model):
    STATUS = [('draft', 'Draft'), ('published', 'Published'), ('closed', 'Closed')]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course_ref = models.CharField(max_length=150, blank=True, verbose_name='Course / Subject Reference')
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    pass_score_pct = models.IntegerField(default=70)
    status = models.CharField(max_length=10, choices=STATUS, default='draft')
    allow_retakes = models.BooleanField(default=True)
    max_attempts = models.PositiveIntegerField(default=3)
    shuffle_questions = models.BooleanField(default=False)
    show_answers_after = models.BooleanField(default=True)
    created_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def total_points(self):
        return sum(q.points for q in self.questions.all())

    def __str__(self):
        return self.title


class Question(models.Model):
    TYPE = [
        ('mc', 'Multiple Choice'),
        ('tf', 'True / False'),
        ('short', 'Short Answer'),
        ('essay', 'Essay / Long Answer'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=10, choices=TYPE, default='mc')
    points = models.DecimalField(max_digits=5, decimal_places=1, default=1)
    order = models.PositiveIntegerField(default=0)
    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:60]}"


class QuestionChoice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    taken_by = models.ForeignKey(BusinessEmployee, on_delete=models.CASCADE, related_name='quiz_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_passed = models.BooleanField(null=True, blank=True)
    attempt_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-started_at']

    @property
    def is_submitted(self):
        return self.submitted_at is not None


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True)
    selected_choice = models.ForeignKey(QuestionChoice, on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    score_earned = models.DecimalField(max_digits=5, decimal_places=1, default=0)
