from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from .models import ForumCategory, ForumTopic, ForumPost, ForumModerationLog

# ─── Permission Helpers ───────────────────────────────────────────────────────

import uuid
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

def can_post(user):
    """
    Allow authenticated `console_user` and `workspace_admin`.
    Unauthenticated users can post if they provide a valid email (handled in the view).
    """
    if not user.is_authenticated:
        return True
    return user.role in ['console_user', 'workspace_admin']

def is_admin(user):
    return user.is_authenticated and user.role == 'workspace_admin'

# ─── AI Moderation Hook ────────────────────────────────────────────────────────

FLAGGED_KEYWORDS = [
    'spam', 'advertisement', 'buy now', 'click here', 'free money',
    'offensive', 'hate', 'abuse', 'scam', 'phishing',
]

def serea_moderate(post):
    """
    Serea's moderation logic (Phase 7 will connect this to a real n8n workflow/LLM).
    For now: keyword-based filtering that flags and escalates posts.
    Returns True if post was flagged.
    """
    content_lower = post.content.lower()
    for keyword in FLAGGED_KEYWORDS:
        if keyword in content_lower:
            post.is_flagged = True
            post.ai_flag_reason = f"Serea detected potentially violating content (keyword: '{keyword}')."
            post.is_escalated = True
            post.is_hidden = True
            post.save()
            # Log the moderation action
            ForumModerationLog.objects.create(
                post=post,
                actor='Serea AI',
                action='ai_escalate',
                reason=post.ai_flag_reason,
            )
            return True
    return False

# ─── Public Views ─────────────────────────────────────────────────────────────

def index(request):
    categories = ForumCategory.objects.all()
    return render(request, 'community_forum/index.html', {'categories': categories})

def category_detail(request, slug):
    category = get_object_or_404(ForumCategory, slug=slug)
    topics = category.topics.order_by('-is_pinned', '-updated_at')
    return render(request, 'community_forum/category_detail.html', {
        'category': category,
        'topics': topics,
        'can_post': can_post(request.user),
    })

def topic_detail(request, pk):
    topic = get_object_or_404(ForumTopic, pk=pk)
    # Only show non-hidden posts to regular users; admins see all
    posts = topic.posts.order_by('created_at')
    if not is_admin(request.user):
        posts = posts.filter(is_hidden=False)
    return render(request, 'community_forum/topic_detail.html', {
        'topic': topic,
        'posts': posts,
        'can_post': can_post(request.user),
        'is_admin': is_admin(request.user),
    })

# ─── Unauthenticated User Helper ──────────────────────────────────────────────

def get_or_create_viewer_user(request, email):
    try:
        validate_email(email)
    except ValidationError:
        return None, "Please use a valid email to post, comment, or reply."

    # Check if a user with this email already exists
    user = User.objects.filter(email=email).first()
    if user:
        return None, "An account with this email already exists. Please log in."

    # Create a new user account for the viewer
    # Generate unique username: viewer_<uuid prefix>
    username = f"viewer_{uuid.uuid4().hex[:8]}"

    # We create the user with role 'console_user' but unverified
    new_user = User.objects.create_user(
        username=username,
        email=email,
        password=User.objects.make_random_password(16),
        role='console_user',
        is_email_verified=False
    )
    return new_user, None

# ─── Posting Views ────────────────────────────────────────────────────────────

def create_topic(request, slug):
    if not can_post(request.user):
        raise PermissionDenied("You do not have permission to post in the forum.")

    category = get_object_or_404(ForumCategory, slug=slug)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        topic_type = request.POST.get('topic_type', 'question')

        author = request.user

        # Handle unauthenticated users submitting email
        if not author.is_authenticated:
            email = request.POST.get('email', '').strip()
            if not email:
                messages.error(request, "Email is required to post.")
                return redirect('create_topic', slug=category.slug)

            new_user, error_msg = get_or_create_viewer_user(request, email)
            if error_msg:
                messages.error(request, error_msg)
                return redirect('create_topic', slug=category.slug)

            author = new_user

        if title and content:
            topic = ForumTopic.objects.create(
                category=category,
                creator=author,
                title=title,
                content=content,
                topic_type=topic_type,
            )
            return redirect('topic_detail', pk=topic.pk)

    return render(request, 'community_forum/create_topic.html', {
        'category': category,
        'topic_types': ForumTopic.TOPIC_TYPES,
        'can_post': can_post(request.user),
    })

def create_post(request, pk):
    if not can_post(request.user):
        raise PermissionDenied("You do not have permission to reply in the forum.")

    topic = get_object_or_404(ForumTopic, pk=pk)

    if topic.is_locked:
        messages.error(request, "This topic is locked and cannot receive new replies.")
        return redirect('topic_detail', pk=topic.pk)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()

        author = request.user
        if not author.is_authenticated:
            email = request.POST.get('email', '').strip()
            if not email:
                messages.error(request, "Email is required to reply.")
                return redirect('topic_detail', pk=topic.pk)

            new_user, error_msg = get_or_create_viewer_user(request, email)
            if error_msg:
                messages.error(request, error_msg)
                return redirect('topic_detail', pk=topic.pk)

            author = new_user

        if content:
            post = ForumPost.objects.create(
                topic=topic, author=author, content=content
            )
            topic.save()  # bumps updated_at
            # 🤖 Serea moderation pass
            flagged = serea_moderate(post)
            if flagged:
                messages.warning(
                    request,
                    "Your reply has been sent for review by our AI moderator (Serea) before it becomes visible."
                )

    return redirect('topic_detail', pk=topic.pk)

def reply_to_post(request, pk):
    """View to handle threading/replies to specific posts"""
    if not can_post(request.user):
        raise PermissionDenied("You do not have permission to reply in the forum.")

    parent_post = get_object_or_404(ForumPost, pk=pk)
    topic = parent_post.topic

    if topic.is_locked:
        messages.error(request, "This topic is locked and cannot receive new replies.")
        return redirect('topic_detail', pk=topic.pk)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()

        author = request.user
        if not author.is_authenticated:
            email = request.POST.get('email', '').strip()
            if not email:
                messages.error(request, "Email is required to reply.")
                return redirect('topic_detail', pk=topic.pk)

            new_user, error_msg = get_or_create_viewer_user(request, email)
            if error_msg:
                messages.error(request, error_msg)
                return redirect('topic_detail', pk=topic.pk)

            author = new_user

        if content:
            post = ForumPost.objects.create(
                topic=topic, parent=parent_post, author=author, content=content
            )
            topic.save()

            flagged = serea_moderate(post)
            if flagged:
                messages.warning(
                    request,
                    "Your reply has been sent for review by our AI moderator (Serea) before it becomes visible."
                )

    return redirect('topic_detail', pk=topic.pk)

# ─── Workspace Admin Moderation ───────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def moderation_panel(request):
    """
    Workspace Admin moderation panel — review flagged posts, pin/lock topics,
    hide/restore posts, and mark questions as solved.
    """
    if not is_admin(request.user):
        raise PermissionDenied("Only Workspace Admins can access the moderation panel.")

    flagged_posts = ForumPost.objects.filter(is_flagged=True).select_related('author', 'topic').order_by('-created_at')
    recent_logs = ForumModerationLog.objects.order_by('-timestamp')[:30]
    all_topics = ForumTopic.objects.select_related('creator', 'category').order_by('-created_at')[:50]

    if request.method == 'POST':
        action = request.POST.get('action')
        post_id = request.POST.get('post_id')
        topic_id = request.POST.get('topic_id')

        if action == 'hide_post' and post_id:
            post = get_object_or_404(ForumPost, id=post_id)
            post.is_hidden = True
            post.moderated_by = request.user
            post.moderated_at = timezone.now()
            post.save()
            ForumModerationLog.objects.create(post=post, actor=request.user.email, action='admin_hide')
            messages.success(request, f"Post #{post_id} hidden.")

        elif action == 'restore_post' and post_id:
            post = get_object_or_404(ForumPost, id=post_id)
            post.is_hidden = False
            post.is_flagged = False
            post.is_escalated = False
            post.moderated_by = request.user
            post.moderated_at = timezone.now()
            post.save()
            ForumModerationLog.objects.create(post=post, actor=request.user.email, action='admin_restore')
            messages.success(request, f"Post #{post_id} restored.")

        elif action == 'lock_topic' and topic_id:
            topic = get_object_or_404(ForumTopic, id=topic_id)
            topic.is_locked = not topic.is_locked
            topic.save()
            action_key = 'admin_lock' if topic.is_locked else 'admin_restore'
            ForumModerationLog.objects.create(topic=topic, actor=request.user.email, action=action_key)
            messages.success(request, f"Topic {'locked' if topic.is_locked else 'unlocked'}.")

        elif action == 'pin_topic' and topic_id:
            topic = get_object_or_404(ForumTopic, id=topic_id)
            topic.is_pinned = not topic.is_pinned
            topic.save()
            ForumModerationLog.objects.create(topic=topic, actor=request.user.email, action='admin_pin')
            messages.success(request, f"Topic {'pinned' if topic.is_pinned else 'unpinned'}.")

        elif action == 'mark_solved' and topic_id:
            topic = get_object_or_404(ForumTopic, id=topic_id)
            topic.is_solved = True
            topic.save()
            ForumModerationLog.objects.create(topic=topic, actor=request.user.email, action='admin_mark_solved')
            messages.success(request, "Topic marked as solved.")

        return redirect('moderation_panel')

    return render(request, 'community_forum/moderation_panel.html', {
        'flagged_posts': flagged_posts,
        'recent_logs': recent_logs,
        'all_topics': all_topics,
    })
