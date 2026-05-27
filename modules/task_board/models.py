from django.db import models
from django.utils import timezone
from accounts.models import User


CARD_COLORS = [
    ('', 'None'),
    ('red', 'Red'),
    ('orange', 'Orange'),
    ('yellow', 'Yellow'),
    ('green', 'Green'),
    ('teal', 'Teal'),
    ('blue', 'Blue'),
    ('indigo', 'Indigo'),
    ('purple', 'Purple'),
    ('pink', 'Pink'),
    ('gray', 'Gray'),
]

BOARD_COLORS = [
    ('default', '#1e293b'),
    ('blue', '#1d4ed8'),
    ('green', '#15803d'),
    ('purple', '#7e22ce'),
    ('red', '#b91c1c'),
    ('orange', '#c2410c'),
    ('teal', '#0f766e'),
    ('indigo', '#4338ca'),
]


class Board(models.Model):
    business = models.ForeignKey(
        'bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='task_boards'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, choices=BOARD_COLORS, default='default')
    is_archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_boards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    def get_card_count(self):
        return Card.objects.filter(board_list__board=self, is_archived=False).count()

    def get_done_count(self):
        done_list = self.lists.filter(name__iexact='done').first()
        if done_list:
            return done_list.cards.filter(is_archived=False).count()
        return 0


class BoardList(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='lists')
    name = models.CharField(max_length=100)
    position = models.IntegerField(default=0)
    task_limit = models.IntegerField(default=0, help_text='0 = unlimited')
    color = models.CharField(max_length=7, blank=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.name} ({self.board.name})"

    def card_count(self):
        return self.cards.filter(is_archived=False).count()

    def is_over_limit(self):
        return self.task_limit > 0 and self.card_count() >= self.task_limit


class Card(models.Model):
    board_list = models.ForeignKey(BoardList, on_delete=models.CASCADE, related_name='cards')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, choices=CARD_COLORS, blank=True)
    position = models.IntegerField(default=0)

    due_date = models.DateField(null=True, blank=True)
    story_points = models.PositiveSmallIntegerField(null=True, blank=True)

    assignees = models.ManyToManyField(
        'bredbound.BusinessEmployee', blank=True, related_name='assigned_cards'
    )

    is_archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_cards'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'created_at']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return self.due_date and self.due_date < timezone.now().date()

    def checklist_progress(self):
        total = ChecklistItem.objects.filter(checklist__card=self).count()
        done = ChecklistItem.objects.filter(checklist__card=self, is_done=True).count()
        return (total, done)


class Label(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='labels')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#3b82f6')

    class Meta:
        unique_together = [('board', 'name')]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.board.name})"


class CardLabel(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='card_labels')
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='card_labels')

    class Meta:
        unique_together = [('card', 'label')]


class Checklist(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='checklists')
    name = models.CharField(max_length=100, default='Checklist')
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'created_at']

    def progress_pct(self):
        total = self.items.count()
        if total == 0:
            return 0
        done = self.items.filter(is_done=True).count()
        return round(done / total * 100)


class ChecklistItem(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=200)
    is_done = models.BooleanField(default=False)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'created_at']

    def __str__(self):
        return self.title


class CardComment(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='board_comments')
    content = models.TextField()
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.email} on {self.card.title}"


class CardActivity(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='activities')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='board_activities')
    event = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event}: {self.description}"
