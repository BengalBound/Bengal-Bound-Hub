"""
serea/logic.py
──────────────
The 'brain' of the Serea AI Social Media Moderator.

Serea is a full-fledged AI Employee — she remembers conversations, takes tasks,
creates posts, generates reports, asks for permission when unsure, and speaks
naturally like a human colleague.

LLM support:
  • NeuroLinkIt — own AI server at https://api.neurolinkit.com (primary/testing)
  • Groq  — free, fast Llama/Gemma/Mixtral models
  • OpenRouter — 10+ free models + paid tier (langchain-openai with custom base_url)
  • OpenAI — GPT-4o / GPT-4o-mini (langchain-openai)

Social Platforms managed: Facebook, Instagram, LinkedIn

Human-in-the-Loop:
  Serea's confidence < CONFIDENCE_THRESHOLD → she calls trigger_permission_request
  instead of acting unilaterally.
"""

import os
import re
import logging
import json
from typing import Optional, Literal

from pydantic import BaseModel, Field

from django.db import models as db_models
from django.utils import timezone

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
from langgraph.prebuilt import create_react_agent

from .models import (
    SereaAgent,
    ConversationMessage,
    AgentInstruction,
    ContentQueue,
    SereaReport,
    SocialMediaAccount,
    ClientContentFile,
    SereaTask,
    CampaignTracker,
    EngagementLog,
    SereaMemory,
    CommunityMemberProfile,
    CustomerServiceThread,
    EscalationRecord,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# EXCEPTIONS
# ─────────────────────────────────────────────────────────────────────────────

class TokenLimitExceeded(Exception):
    """Raised when an agent has consumed its monthly token budget."""


# ─────────────────────────────────────────────────────────────────────────────
# TOKEN TRACKING CALLBACK
# ─────────────────────────────────────────────────────────────────────────────

class _TokenCounterCallback(BaseCallbackHandler):
    """
    LangChain callback that sums total tokens across all LLM calls in one
    agent run. Works for Groq, OpenAI, and OpenRouter response formats.
    """

    def __init__(self):
        super().__init__()
        self.total_tokens: int = 0

    def on_llm_end(self, response, **kwargs) -> None:
        if hasattr(response, 'llm_output') and response.llm_output:
            usage = response.llm_output.get('token_usage', {})
            self.total_tokens += (
                usage.get('total_tokens', 0)
                or usage.get('prompt_tokens', 0) + usage.get('completion_tokens', 0)
            )


# ─────────────────────────────────────────────────────────────────────────────
# TOOLS  (module-level; each accepts agent_id: str so it can look up the DB)
# ─────────────────────────────────────────────────────────────────────────────

@tool
def trigger_permission_request(agent_id: str, context: str, suggestion_a: str = '', suggestion_b: str = '') -> str:
    """
    Use this when you need your employer's input before taking an action —
    either because you're unsure what they'd want, or because the action is
    significant enough that they should know about it first.

    This posts a message in the console chat and waits for their Approve/Deny.
    After calling this tool, do NOT take the action — hold off until they respond.

    Write the context naturally, like you're messaging a colleague. Include your
    thinking and, if possible, two options so they can just pick one.

    Args:
        agent_id:     The SereaAgent ID (as string).
        context:      What happened, what you're thinking, and why you're checking in.
                      Write this as a natural message, NOT a formal report.
        suggestion_a: Your preferred option / what you'd recommend doing.
        suggestion_b: An alternative option they could choose instead.
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))

        # Build a natural, human-feeling message
        parts = [context.strip()]

        if suggestion_a and suggestion_b:
            parts.append(
                f"\n\nHere's how I see it:\n"
                f"**Option A** (what I'd go with): {suggestion_a}\n"
                f"**Option B**: {suggestion_b}\n\n"
                "Approve if you're happy with Option A, or Deny and drop me a message "
                "if you'd rather do Option B or something else."
            )
        elif suggestion_a:
            parts.append(
                f"\n\nMy plan: {suggestion_a}\n\n"
                "Hit Approve if that sounds good, Deny if you'd rather I hold off."
            )
        else:
            parts.append(
                "\n\nLetting you know before I do anything — Approve to go ahead, "
                "Deny if you'd rather I leave it."
            )

        msg_text = ''.join(parts)

        ConversationMessage.objects.create(
            agent=agent,
            sender='serea',
            message_text=msg_text,
            is_permission_request=True,
            pending_action_context={
                'raw_context': context,
                'suggestion_a': suggestion_a,
                'suggestion_b': suggestion_b,
            },
        )
        agent.status = 'waiting'
        agent.save(update_fields=['status'])
        return "Permission request sent — holding off until you hear back."
    except SereaAgent.DoesNotExist:
        return f"ERROR: SereaAgent id={agent_id} not found."
    except Exception as exc:
        logger.error("trigger_permission_request error: %s", exc)
        return f"ERROR: {exc}"


@tool
def create_social_post(
    agent_id: str,
    platform: str,
    caption: str,
    hashtags: str = '',
    schedule_time: str = '',
) -> str:
    """
    Creates and schedules a social media post in the content queue.
    Use this whenever the client asks you to write or schedule a post.

    Args:
        agent_id:      The SereaAgent ID (as string).
        platform:      Target platform — Instagram, Facebook, Twitter, LinkedIn, TikTok, YouTube.
        caption:       The full post caption / body text you have written.
        hashtags:      Space or comma-separated hashtags (e.g. "#brand #sale"). Optional.
        schedule_time: When to post in "YYYY-MM-DD HH:MM" UTC format.
                       Leave empty to schedule as soon as possible.

    Returns a confirmation with the post ID and scheduled time.
    """
    from django.utils.dateparse import parse_datetime
    import datetime

    try:
        agent = SereaAgent.objects.get(id=int(agent_id))

        if schedule_time:
            post_date = parse_datetime(schedule_time)
            if post_date is None:
                post_date = timezone.now() + datetime.timedelta(hours=1)
        else:
            post_date = timezone.now() + datetime.timedelta(minutes=5)

        item = ContentQueue.objects.create(
            agent=agent,
            title=f"{platform} — {post_date.strftime('%b %d %Y')}",
            platform=platform,
            caption=caption,
            hashtags=hashtags,
            post_date=post_date,
            status='pending',
        )
        return (
            f"Post scheduled! ID #{item.id} on {platform} at "
            f"{post_date.strftime('%b %d %Y %H:%M UTC')}.\n"
            f"Caption preview: {caption[:80]}{'...' if len(caption) > 80 else ''}"
        )
    except Exception as exc:
        logger.error("create_social_post error: %s", exc)
        return f"ERROR scheduling post: {exc}"


@tool
def list_scheduled_posts(agent_id: str) -> str:
    """
    Lists upcoming scheduled posts in the content queue.
    Use this when the client asks what's coming up or what's been scheduled.

    Args:
        agent_id: The SereaAgent ID (as string).
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        pending = agent.content_queue.filter(status='pending').order_by('post_date')[:15]
        if not pending.exists():
            return "Nothing scheduled yet — the content queue is empty."
        lines = ["Upcoming scheduled posts:"]
        for item in pending:
            lines.append(
                f"  #{item.id} [{item.platform}] {item.title} "
                f"— {item.post_date.strftime('%b %d %Y %H:%M UTC')}"
            )
        return '\n'.join(lines)
    except Exception as exc:
        return f"ERROR fetching scheduled posts: {exc}"


@tool
def check_moderation_stats(agent_id: str) -> str:
    """
    Returns a quick moderation statistics summary for this calendar month.
    Use this when the client asks how things are going, about performance,
    or wants a status update.

    Args:
        agent_id: The SereaAgent ID (as string).
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        logs = agent.moderation_logs.filter(created_at__gte=month_start)

        total = logs.count()
        breakdown = {
            'deleted': logs.filter(action_taken='delete').count(),
            'replied': logs.filter(action_taken='reply').count(),
            'flagged':  logs.filter(action_taken='flag').count(),
            'ignored':  logs.filter(action_taken='ignore').count(),
            'pending':  logs.filter(requires_human=True).count(),
        }
        conf_scores = list(
            logs.exclude(confidence_score__isnull=True)
                .values_list('confidence_score', flat=True)
        )
        avg_conf = sum(conf_scores) / len(conf_scores) if conf_scores else None

        posts_pending  = agent.content_queue.filter(status='pending').count()
        posts_published = agent.content_queue.filter(
            status='posted', created_at__gte=month_start
        ).count()

        lines = [f"Moderation stats for {now.strftime('%B %Y')}:"]
        lines.append(f"  Total actions: {total}")
        for action, count in breakdown.items():
            if count:
                lines.append(f"    {action}: {count}")
        if avg_conf is not None:
            lines.append(f"  Average confidence: {avg_conf:.0%}")
        lines.append(f"  Content queue: {posts_pending} pending, {posts_published} published this month")
        lines.append(f"  Tokens used this month: {agent.tokens_used_this_month:,}")
        return '\n'.join(lines)
    except Exception as exc:
        return f"ERROR fetching stats: {exc}"


@tool
def generate_report(
    agent_id: str,
    report_type: str,
    period: str = 'this_month',
    extra_notes: str = '',
) -> str:
    """
    Compiles an activity report from the database and saves it as a SereaReport.
    Use this when the client asks for a report, summary, or recap of activity.

    Args:
        agent_id:    The SereaAgent ID (as string).
        report_type: One of: daily, weekly, moderation, content, custom.
        period:      One of: today, yesterday, this_week, last_week, this_month, last_month.
        extra_notes: Any additional context to include in the report body.

    Returns a data summary that you should format into a polished report.
    """
    import datetime

    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        now = timezone.now()

        if period == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == 'yesterday':
            end = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start = end - datetime.timedelta(days=1)
        elif period == 'this_week':
            start = now - datetime.timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == 'last_week':
            end = now - datetime.timedelta(days=now.weekday())
            end = end.replace(hour=0, minute=0, second=0, microsecond=0)
            start = end - datetime.timedelta(days=7)
        elif period == 'last_month':
            first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = first_of_month
            start = (first_of_month - datetime.timedelta(days=1)).replace(day=1)
        else:  # this_month (default)
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now

        logs = agent.moderation_logs.filter(created_at__gte=start, created_at__lte=end)
        total = logs.count()
        breakdown = {
            'deleted':  logs.filter(action_taken='delete').count(),
            'replied':  logs.filter(action_taken='reply').count(),
            'flagged':  logs.filter(action_taken='flag').count(),
            'ignored':  logs.filter(action_taken='ignore').count(),
            'pending_human': logs.filter(requires_human=True).count(),
        }

        conf_scores = list(
            logs.exclude(confidence_score__isnull=True)
                .values_list('confidence_score', flat=True)
        )
        avg_conf = sum(conf_scores) / len(conf_scores) if conf_scores else None

        posts_scheduled  = agent.content_queue.filter(created_at__gte=start, created_at__lte=end).count()
        posts_published  = agent.content_queue.filter(
            status='posted', created_at__gte=start, created_at__lte=end
        ).count()
        posts_pending    = agent.content_queue.filter(status='pending').count()

        raw_data = {
            'period': f"{start.strftime('%b %d')} – {end.strftime('%b %d %Y')}",
            'moderation_total': total,
            'moderation_breakdown': breakdown,
            'avg_confidence': f"{avg_conf:.0%}" if avg_conf is not None else 'N/A',
            'posts_scheduled': posts_scheduled,
            'posts_published': posts_published,
            'posts_pending_queue': posts_pending,
            'tokens_used_month': agent.tokens_used_this_month,
            'extra_notes': extra_notes,
        }
        return json.dumps(raw_data)

    except Exception as exc:
        logger.error("generate_report data error: %s", exc)
        return f"ERROR fetching report data: {exc}"


@tool
def save_report(agent_id: str, report_type: str, title: str, body: str) -> str:
    """
    Saves a finished report to the database so the client can refer back to it.
    Always call this AFTER you have formatted the report into polished text.

    Args:
        agent_id:    The SereaAgent ID (as string).
        report_type: One of: daily, weekly, moderation, content, custom.
        title:       Short descriptive title (e.g. "Weekly Moderation Summary – Mar 10-16").
        body:        The complete formatted report text.
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        report = SereaReport.objects.create(
            agent=agent,
            report_type=report_type,
            title=title,
            body=body,
        )
        # Also post as a conversation message so the client sees it in chat
        ConversationMessage.objects.create(
            agent=agent,
            sender='serea',
            message_text=f"📊 **{title}**\n\n{body}",
        )
        return f"Report saved (ID #{report.id}) and posted to your chat."
    except Exception as exc:
        logger.error("save_report error: %s", exc)
        return f"ERROR saving report: {exc}"


@tool
def save_client_instruction(agent_id: str, instruction: str) -> str:
    """
    Saves a new instruction or preference that the client gives Serea.
    Use this when the client tells you to always/never do something,
    or sets a rule for how you should handle specific situations.

    Args:
        agent_id:    The SereaAgent ID (as string).
        instruction: The instruction text to remember permanently.
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        AgentInstruction.objects.create(agent=agent, instruction_text=instruction, is_active=True)
        return f"Got it! I've saved that as a permanent instruction: \"{instruction}\""
    except Exception as exc:
        logger.error("save_client_instruction error: %s", exc)
        return f"ERROR saving instruction: {exc}"


@tool
def check_onboarding_status(agent_id: str) -> str:
    """
    Returns the current setup status for this Serea agent.
    Call this at the START of any new conversation to understand what is already
    set up and what still needs to be configured.

    Returns a JSON object with:
      - onboarding_complete: whether setup is done
      - platforms: list of connected social media accounts
      - content_files: count and types of uploaded business knowledge
      - has_instructions: whether the client has given Serea custom rules
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        platforms = agent.social_accounts.filter(is_active=True).values(
            'platform', 'account_name', 'status', 'page_bio'
        )
        content_files = agent.content_files.filter(is_active=True)
        status = {
            'onboarding_complete': agent.onboarding_complete,
            'platforms_connected': list(platforms),
            'platforms_count': len(list(platforms)),
            'content_files_count': content_files.count(),
            'content_types_available': list(
                content_files.values_list('content_type', flat=True)
            ),
            'has_custom_instructions': agent.instructions.filter(is_active=True).exists(),
            'agent_tier': agent.get_tier_display(),
            'platform_connection_url': '/platforms/',
            'workspace_url': '/workspace/',
        }
        return json.dumps(status, indent=2)
    except Exception as exc:
        return f"ERROR: {exc}"


@tool
def get_business_knowledge(agent_id: str, query: str = '') -> str:
    """
    Searches the client's uploaded content files for business knowledge.
    Use this when:
      - Answering questions about the business, products, or services
      - Writing posts or captions (to match brand voice and product details)
      - Deciding how to reply to comments or DMs
      - Checking what tone or language the client wants you to use

    Args:
        agent_id: The SereaAgent ID.
        query:    Optional keyword to filter relevant content (e.g. 'pricing', 'FAQ', 'tone').
                  Leave blank to retrieve all available content.
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        files = agent.content_files.filter(is_active=True)

        if not files.exists():
            return (
                "No business content has been uploaded yet. "
                "Ask the client to go to the Workspace section and upload their content "
                "(product info, FAQs, tone guide, response templates, etc.)."
            )

        results = []
        for f in files:
            content = f.get_content_for_injection()
            if not content:
                continue
            # Filter by query if provided
            if query and query.lower() not in content.lower() and query.lower() not in f.title.lower():
                continue
            results.append(
                f"[{f.get_content_type_display()}] **{f.title}**\n{content[:1500]}"
            )

        if not results:
            available = ', '.join(files.values_list('title', flat=True))
            return f"No content matched '{query}'. Available files: {available}"

        return '\n\n---\n\n'.join(results[:4])  # Return up to 4 most relevant
    except Exception as exc:
        logger.error("get_business_knowledge error: %s", exc)
        return f"ERROR: {exc}"


@tool
def get_my_tasks(agent_id: str) -> str:
    """
    Returns your current task list — active tasks, their status, priority, and due dates.
    Call this when the client asks what you're working on, how things are going,
    or when you want to give a status update.

    Args:
        agent_id: The SereaAgent ID.
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        tasks = agent.serea_tasks.all().order_by('status', '-priority', 'created_at')
        if not tasks.exists():
            return "No tasks assigned yet."

        active = tasks.exclude(status__in=['done', 'cancelled'])
        done   = tasks.filter(status='done')
        lines  = []

        if active.exists():
            lines.append("Active tasks:")
            for t in active:
                due = f" (due {t.due_date.strftime('%b %d')})" if t.due_date else ''
                notes = f"\n   Notes: {t.progress_notes[:120]}" if t.progress_notes else ''
                lines.append(
                    f"  #{t.id} [{t.get_priority_display()}] {t.title} — {t.get_status_display()}{due}{notes}"
                )

        if done.exists():
            lines.append(f"\nCompleted ({done.count()} tasks)")

        return '\n'.join(lines)
    except Exception as exc:
        return f"ERROR: {exc}"


@tool
def create_task(agent_id: str, title: str, description: str = '', priority: str = 'normal') -> str:
    """
    Creates a new task for yourself when the client assigns something in chat.
    Use this any time the client asks you to do something that isn't instant —
    anything that takes research, time, or multiple steps.

    Args:
        agent_id:    The SereaAgent ID.
        title:       Short task title (e.g. "Write 3 Instagram posts for product launch").
        description: More detail about what needs to be done.
        priority:    One of: low, normal, high, urgent.
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        task = SereaTask.objects.create(
            agent=agent,
            title=title,
            description=description,
            priority=priority,
            status='in_progress',
        )
        return (
            f"Task created! #{task.id} — \"{title}\" "
            f"[{task.get_priority_display()}]. I'm on it."
        )
    except Exception as exc:
        return f"ERROR creating task: {exc}"


@tool
def update_task(agent_id: str, task_id: str, status: str, notes: str = '', result: str = '') -> str:
    """
    Updates a task's status and adds progress notes or a final result.
    Use this to keep the client informed as you work through tasks.

    Args:
        agent_id: The SereaAgent ID.
        task_id:  The SereaTask ID.
        status:   One of: todo, in_progress, waiting_approval, waiting_info, done, cancelled.
        notes:    Brief update on progress or what's blocking you.
        result:   Final output / summary (for when status=done).
    """
    import datetime

    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        task = SereaTask.objects.get(id=int(task_id), agent=agent)
        task.status = status
        if notes:
            task.progress_notes = notes
        if result:
            task.result = result
        if status == 'done' and not task.completed_at:
            task.completed_at = timezone.now()
        task.save()
        return f"Task #{task_id} updated to '{task.get_status_display()}'."
    except SereaTask.DoesNotExist:
        return f"ERROR: Task #{task_id} not found."
    except Exception as exc:
        return f"ERROR: {exc}"


@tool
def mark_onboarding_complete(agent_id: str) -> str:
    """
    Marks the agent's onboarding as complete.
    Call this ONLY once the client has connected at least one social media platform
    AND has uploaded at least one piece of business content.
    This stops the onboarding guidance from appearing in future conversations.

    Args:
        agent_id: The SereaAgent ID.
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        has_platforms = agent.social_accounts.filter(is_active=True).exists()
        has_content = agent.content_files.filter(is_active=True).exists()

        if not has_platforms:
            return (
                "Cannot complete onboarding — no social media platforms are connected yet. "
                "Ask the client to add their platform credentials in the Platforms section."
            )
        if not has_content:
            return (
                "Cannot complete onboarding — no business content has been uploaded yet. "
                "Ask the client to add content (FAQs, product info, tone guide) in the Workspace section."
            )

        agent.onboarding_complete = True
        agent.save(update_fields=['onboarding_complete'])
        return (
            "Onboarding marked as complete! I'm fully set up and ready to manage "
            "your social media. I'll start monitoring and engaging right away."
        )
    except Exception as exc:
        return f"ERROR: {exc}"


@tool
def read_google_sheet(sheet_url: str) -> str:
    """
    Reads post metadata (caption, hashtags, scheduled date, target platform)
    from a Google Sheet linked to the content calendar.
    Returns the sheet data as a JSON-formatted string.
    Requires GOOGLE_SERVICE_ACCOUNT_JSON environment variable.
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        service_account_info = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '{}'))
        if not service_account_info:
            return "ERROR: GOOGLE_SERVICE_ACCOUNT_JSON env var not set."

        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_url(sheet_url)
        worksheet = sh.get_active_sheet()
        records = worksheet.get_all_records()
        return json.dumps(records[:50])
    except Exception as exc:
        logger.error("read_google_sheet error: %s", exc)
        return f"ERROR reading sheet: {exc}"


@tool
def interact_with_drive(folder_url: str) -> str:
    """
    Lists or retrieves visual content (images/videos) from a Google Drive folder.
    Returns a JSON list of file names and their download URLs.
    Requires GOOGLE_SERVICE_ACCOUNT_JSON environment variable.
    """
    try:
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials

        scopes = ['https://www.googleapis.com/auth/drive.readonly']
        service_account_info = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '{}'))
        if not service_account_info:
            return "ERROR: GOOGLE_SERVICE_ACCOUNT_JSON env var not set."

        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        service = build('drive', 'v3', credentials=creds)
        folder_id = folder_url.rstrip('/').split('/')[-1]
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, mimeType, webContentLink)",
            pageSize=20
        ).execute()
        return json.dumps(results.get('files', []))
    except Exception as exc:
        logger.error("interact_with_drive error: %s", exc)
        return f"ERROR accessing Drive: {exc}"


@tool
def log_engagement_action(
    agent_id: str,
    platform: str,
    action: str,
    target_account: str = '',
    target_url: str = '',
    notes: str = '',
    campaign_id: str = '',
) -> str:
    """
    Logs an engagement action you've taken on social media — liking, following,
    commenting, sharing, sending a DM, replying to a mention, etc.
    Use this every time you interact with external accounts or content.

    Args:
        agent_id:       The SereaAgent ID.
        platform:       The platform (facebook, instagram, linkedin).
        action:         One of: like, comment, follow, unfollow, share, dm_sent,
                        mention_reply, story_react, poll_vote, other.
        target_account: The account handle or post owner you interacted with.
        target_url:     URL of the post or profile (optional).
        notes:          Brief reason for this action (e.g. 'Engaged with relevant hashtag post').
        campaign_id:    Link to a CampaignTracker ID if this is part of a campaign (optional).
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        campaign = None
        if campaign_id:
            try:
                campaign = CampaignTracker.objects.get(id=int(campaign_id), agent=agent)
            except CampaignTracker.DoesNotExist:
                pass

        log = EngagementLog.objects.create(
            agent=agent,
            platform=platform,
            action=action,
            target_account=target_account,
            target_url=target_url or None,
            notes=notes,
            campaign=campaign,
        )
        return f"Engagement logged (ID #{log.id}): {action} on {platform} → {target_account or 'target'}."
    except Exception as exc:
        logger.error("log_engagement_action error: %s", exc)
        return f"ERROR logging engagement: {exc}"


@tool
def create_campaign(
    agent_id: str,
    name: str,
    platforms: str,
    goal: str = '',
    description: str = '',
    hashtags: str = '',
    start_date: str = '',
    end_date: str = '',
) -> str:
    """
    Creates a new social media campaign tracker.
    Use this when starting any focused campaign — product launch, event, sale,
    awareness drive, follower growth push, etc.

    Args:
        agent_id:    The SereaAgent ID.
        name:        Campaign name (e.g. 'Summer Sale 2025').
        platforms:   Comma-separated platforms (e.g. 'facebook,instagram,linkedin').
        goal:        Campaign goal (e.g. 'Increase followers by 20%').
        description: What this campaign is about.
        hashtags:    Campaign-specific hashtags (e.g. '#summersale #brand').
        start_date:  YYYY-MM-DD format. Optional.
        end_date:    YYYY-MM-DD format. Optional.
    """
    from django.utils.dateparse import parse_date

    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        platform_list = [p.strip().lower() for p in platforms.split(',') if p.strip()]
        campaign = CampaignTracker.objects.create(
            agent=agent,
            name=name,
            description=description,
            platforms=platform_list,
            goal=goal,
            hashtags=hashtags,
            start_date=parse_date(start_date) if start_date else None,
            end_date=parse_date(end_date) if end_date else None,
            status='planning',
        )
        return (
            f"Campaign created! ID #{campaign.id} — \"{name}\" "
            f"[{', '.join(platform_list)}]. Goal: {goal or 'Not set'}."
        )
    except Exception as exc:
        logger.error("create_campaign error: %s", exc)
        return f"ERROR creating campaign: {exc}"


@tool
def update_campaign(
    agent_id: str,
    campaign_id: str,
    status: str = '',
    progress_notes: str = '',
    results_summary: str = '',
) -> str:
    """
    Updates a campaign's status and adds progress notes or final results.
    Use this as you execute campaign tasks to keep the client informed.

    Args:
        agent_id:        The SereaAgent ID.
        campaign_id:     The CampaignTracker ID.
        status:          One of: planning, active, paused, completed, cancelled.
        progress_notes:  What you've done / what's next.
        results_summary: Final results (use when marking as completed).
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        campaign = CampaignTracker.objects.get(id=int(campaign_id), agent=agent)
        if status:
            campaign.status = status
        if progress_notes:
            campaign.progress_notes = progress_notes
        if results_summary:
            campaign.results_summary = results_summary
        campaign.save()
        return f"Campaign #{campaign_id} '{campaign.name}' updated to [{campaign.get_status_display()}]."
    except CampaignTracker.DoesNotExist:
        return f"ERROR: Campaign #{campaign_id} not found."
    except Exception as exc:
        return f"ERROR: {exc}"


@tool
def get_campaigns(agent_id: str) -> str:
    """
    Returns all active and recent campaigns for this agent.
    Call this when the client asks about ongoing campaigns or campaign status.

    Args:
        agent_id: The SereaAgent ID.
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        campaigns = agent.campaigns.all().order_by('-created_at')[:10]
        if not campaigns.exists():
            return "No campaigns created yet."
        lines = []
        for c in campaigns:
            dates = ''
            if c.start_date:
                dates = f" [{c.start_date} → {c.end_date or 'ongoing'}]"
            lines.append(
                f"  #{c.id} [{c.get_status_display()}] {c.name}{dates}\n"
                f"     Platforms: {', '.join(c.platforms) or 'not set'}  |  Goal: {c.goal[:80] or 'not set'}"
            )
        return "Campaigns:\n" + '\n'.join(lines)
    except Exception as exc:
        return f"ERROR: {exc}"


@tool
def research_hashtags(agent_id: str, topic: str, platform: str = 'instagram') -> str:
    """
    Suggests relevant hashtags for a topic based on the client's business knowledge
    and the target platform's conventions.
    Use this when creating posts or planning campaigns.

    Args:
        agent_id: The SereaAgent ID.
        topic:    The post topic or campaign theme (e.g. 'product launch', 'summer sale').
        platform: Target platform (facebook, instagram, linkedin). Defaults to instagram.
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        business_files = agent.content_files.filter(is_active=True).values_list(
            'title', 'parsed_content', 'manual_text'
        )
        business_context = ' '.join(
            f"{title}: {(parsed or manual)[:200]}"
            for title, parsed, manual in business_files
        )[:600]

        platform_tips = {
            'instagram': (
                "Instagram: use 5–15 hashtags per post. Mix popular (#love, 1M+ posts) "
                "with niche (#yourbrand, <100K posts). Include location hashtags if relevant."
            ),
            'facebook': (
                "Facebook: use 1–3 hashtags max. Focus on brand and campaign hashtags. "
                "Over-hashtagging hurts reach on Facebook."
            ),
            'linkedin': (
                "LinkedIn: use 3–5 professional hashtags. Focus on industry, skill, "
                "and topic hashtags. Example: #marketing #b2b #leadership."
            ),
        }
        tip = platform_tips.get(platform.lower(), platform_tips['instagram'])

        return (
            f"Hashtag research for '{topic}' on {platform.capitalize()}:\n\n"
            f"Platform guidance: {tip}\n\n"
            f"Based on the business context ({business_context[:300] or 'no content uploaded yet'}), "
            f"suggested hashtag categories:\n"
            f"  • Brand: #[yourbrand] #[productname]\n"
            f"  • Topic: #{topic.replace(' ', '')} #{topic.replace(' ', '')}tips\n"
            f"  • Industry: use your industry niche keyword as a hashtag\n"
            f"  • Campaign: create a unique campaign hashtag like #[brand][campaign]\n\n"
            f"Tip: Research competitors' top posts for hashtag inspiration and track which "
            f"hashtags drive the most engagement each month."
        )
    except Exception as exc:
        return f"ERROR researching hashtags: {exc}"


@tool
def edit_scheduled_post(
    agent_id: str,
    post_id: str,
    caption: str = '',
    hashtags: str = '',
    schedule_time: str = '',
    cancel: str = 'no',
) -> str:
    """
    Edits or cancels a scheduled post in the content queue.
    Use this when the client wants to change a post's content or timing,
    or cancel it entirely.

    Args:
        agent_id:      The SereaAgent ID.
        post_id:       The ContentQueue item ID.
        caption:       New caption text (leave empty to keep existing).
        hashtags:      New hashtags (leave empty to keep existing).
        schedule_time: New scheduled time in 'YYYY-MM-DD HH:MM' format.
        cancel:        Set to 'yes' to cancel/delete the post.
    """
    from django.utils.dateparse import parse_datetime

    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        item = ContentQueue.objects.get(id=int(post_id), agent=agent, status='pending')

        if cancel.lower() == 'yes':
            item.delete()
            return f"Post #{post_id} has been cancelled and removed from the queue."

        if caption:
            item.caption = caption
        if hashtags:
            item.hashtags = hashtags
        if schedule_time:
            new_time = parse_datetime(schedule_time)
            if new_time:
                item.post_date = new_time
        item.save()
        return (
            f"Post #{post_id} updated. "
            f"Scheduled: {item.post_date.strftime('%b %d %Y %H:%M UTC')}."
        )
    except ContentQueue.DoesNotExist:
        return f"ERROR: Post #{post_id} not found or already published."
    except Exception as exc:
        return f"ERROR editing post: {exc}"


@tool
def get_engagement_summary(agent_id: str, platform: str = '', days: int = 7) -> str:
    """
    Returns a summary of engagement actions taken in the last N days.
    Use this when the client asks what outreach has been done or wants
    to review engagement activity.

    Args:
        agent_id: The SereaAgent ID.
        platform: Filter by platform (facebook, instagram, linkedin). Empty = all.
        days:     How many days back to look. Default 7.
    """
    import datetime

    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        since = timezone.now() - datetime.timedelta(days=days)
        logs = agent.engagement_logs.filter(created_at__gte=since)
        if platform:
            logs = logs.filter(platform__iexact=platform)

        if not logs.exists():
            return f"No engagement activity logged in the last {days} days."

        by_action: dict = {}
        for log in logs:
            by_action[log.action] = by_action.get(log.action, 0) + 1

        lines = [f"Engagement summary — last {days} days{' on ' + platform if platform else ''}:"]
        for action, count in sorted(by_action.items(), key=lambda x: -x[1]):
            lines.append(f"  {action}: {count}")
        lines.append(f"  Total: {logs.count()} actions")
        return '\n'.join(lines)
    except Exception as exc:
        return f"ERROR: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# MEMORY TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@tool
def save_memory(
    agent_id: str,
    subject: str,
    content: str,
    memory_type: str = 'general',
    importance: str = 'medium',
    platform: str = '',
) -> str:
    """
    Save something important to your long-term memory so you remember it
    across future sessions, Celery runs, and chat conversations.

    Use this for:
    • Things the employer explicitly tells you to remember
    • Patterns you notice (e.g. "Monday posts always get low engagement")
    • User behaviour notes (e.g. "user @xyz always comments negatively then backs off")
    • Brand voice rules you've learned from feedback
    • Anything that would be genuinely useful to recall later

    Args:
        agent_id:    Your SereaAgent ID (as string).
        subject:     Short label for what this memory is about.
                     e.g. "user:@spammy_handle", "brand tone", "FB engagement pattern"
        content:     What to remember — be specific enough to be useful later.
        memory_type: One of: user, brand, community, customer, offender, general
        importance:  One of: low, medium, high, critical
        platform:    Platform this relates to (leave blank for cross-platform memories).
    """
    valid_types = {'user', 'brand', 'community', 'customer', 'offender', 'general'}
    valid_importance = {'low', 'medium', 'high', 'critical'}
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        mem_type = memory_type if memory_type in valid_types else 'general'
        imp = importance if importance in valid_importance else 'medium'

        # Upsert: update existing memory for same subject if it exists
        mem, created = SereaMemory.objects.update_or_create(
            agent=agent,
            subject=subject,
            memory_type=mem_type,
            defaults={
                'content': content,
                'importance': imp,
                'platform': platform,
                'is_active': True,
            },
        )
        action = 'Saved' if created else 'Updated'
        return f"{action} memory: [{mem_type}] {subject}"
    except SereaAgent.DoesNotExist:
        return f"ERROR: SereaAgent id={agent_id} not found."
    except Exception as exc:
        return f"ERROR saving memory: {exc}"


@tool
def recall_memories(
    agent_id: str,
    query: str,
    memory_type: str = '',
) -> str:
    """
    Search your long-term memory for anything relevant to the current situation.

    Use this before responding to recurring users, when handling a topic you've
    dealt with before, or whenever context from a previous session would help.

    Args:
        agent_id:    Your SereaAgent ID (as string).
        query:       What you're looking for — a username, topic, platform, keyword.
        memory_type: Optional filter: user, brand, community, customer, offender, general
    """
    try:
        from django.db.models import Q
        agent = SereaAgent.objects.get(id=int(agent_id))
        now = timezone.now()

        qs = agent.memories.filter(
            is_active=True,
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )
        if memory_type:
            qs = qs.filter(memory_type=memory_type)
        qs = qs.filter(
            Q(subject__icontains=query) | Q(content__icontains=query)
        ).order_by('-importance', '-updated_at')[:10]

        if not qs.exists():
            return f"No memories found matching '{query}'."

        lines = [f"Memory results for '{query}':"]
        for m in qs:
            platform_tag = f" [{m.platform}]" if m.platform else ""
            lines.append(
                f"  [{m.get_memory_type_display()}{platform_tag} | {m.importance}] "
                f"{m.subject}: {m.content[:250]}"
            )
        return '\n'.join(lines)
    except SereaAgent.DoesNotExist:
        return f"ERROR: SereaAgent id={agent_id} not found."
    except Exception as exc:
        return f"ERROR recalling memories: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# COMMUNITY MANAGEMENT TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@tool
def get_or_create_member(
    agent_id: str,
    platform: str,
    platform_user_id: str,
    username: str,
    display_name: str = '',
) -> str:
    """
    Look up a community member's profile — or create one if this is their first interaction.

    Use this whenever a user comments, sends a DM, or you want to check their history
    before deciding how to respond. Tells you whether they're new, flagged, or a repeat offender.

    Args:
        agent_id:         Your SereaAgent ID (as string).
        platform:         Platform: facebook, instagram, or linkedin.
        platform_user_id: The user's ID on the platform.
        username:         Their @handle or display name.
        display_name:     Their full name if available (optional).
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        profile, created = CommunityMemberProfile.objects.get_or_create(
            agent=agent,
            platform=platform,
            platform_user_id=platform_user_id,
            defaults={'username': username, 'display_name': display_name},
        )
        if not created and username:
            # Keep username fresh
            profile.username = username
            if display_name:
                profile.display_name = display_name
            profile.save(update_fields=['username', 'display_name', 'last_seen_at'])

        status = 'NEW' if created else 'RETURNING'
        flags = ''
        if profile.is_blocked:
            flags = ' | STATUS: BLOCKED'
        elif profile.is_flagged:
            flags = f' | STATUS: FLAGGED — {profile.flag_reason[:80]}'

        return (
            f"Member: @{profile.username} on {platform} [{status}]{flags}\n"
            f"Violations: {profile.violation_count} | "
            f"Engagement score: {profile.engagement_score:.1f}/1.0 | "
            f"Welcomed: {'yes' if profile.welcomed_at else 'no'}\n"
            f"Notes: {profile.notes[:200] or 'none'}"
        )
    except SereaAgent.DoesNotExist:
        return f"ERROR: SereaAgent id={agent_id} not found."
    except Exception as exc:
        return f"ERROR: {exc}"


@tool
def update_member(
    agent_id: str,
    platform: str,
    platform_user_id: str,
    notes: str = '',
    flag_action: str = '',
    flag_reason: str = '',
    add_violation: bool = False,
    engagement_score: float = -1.0,
) -> str:
    """
    Update a community member's profile — add notes, flag them, adjust their engagement score,
    or record a violation.

    Args:
        agent_id:          Your SereaAgent ID (as string).
        platform:          Platform: facebook, instagram, or linkedin.
        platform_user_id:  The user's platform ID.
        notes:             New notes to append to their profile.
        flag_action:       'flag' to put them on watch, 'unflag' to clear, 'block' to block.
        flag_reason:       Why you're flagging them (required if flag_action='flag' or 'block').
        add_violation:     True to increment their violation count by 1.
        engagement_score:  New score between 0.0 and 1.0 (-1.0 = no change).
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        profile = CommunityMemberProfile.objects.get(
            agent=agent, platform=platform, platform_user_id=platform_user_id
        )

        update_fields = ['last_seen_at']

        if notes:
            sep = '\n' if profile.notes else ''
            profile.notes = f"{profile.notes}{sep}{notes}"
            update_fields.append('notes')

        if add_violation:
            profile.violation_count += 1
            update_fields.append('violation_count')

        if flag_action == 'flag':
            profile.is_flagged = True
            profile.flag_reason = flag_reason
            update_fields += ['is_flagged', 'flag_reason']
        elif flag_action == 'unflag':
            profile.is_flagged = False
            profile.flag_reason = ''
            update_fields += ['is_flagged', 'flag_reason']
        elif flag_action == 'block':
            profile.is_blocked = True
            profile.is_flagged = True
            profile.flag_reason = flag_reason or 'Blocked by Serea'
            update_fields += ['is_blocked', 'is_flagged', 'flag_reason']

        if 0.0 <= engagement_score <= 1.0:
            profile.engagement_score = engagement_score
            update_fields.append('engagement_score')

        profile.save(update_fields=update_fields)
        return (
            f"Updated @{profile.username} on {platform}. "
            f"Violations: {profile.violation_count}, "
            f"Flagged: {profile.is_flagged}, Blocked: {profile.is_blocked}"
        )
    except CommunityMemberProfile.DoesNotExist:
        return (
            f"No profile found for user {platform_user_id} on {platform}. "
            "Use get_or_create_member first."
        )
    except Exception as exc:
        return f"ERROR: {exc}"


@tool
def welcome_new_member(
    agent_id: str,
    platform: str,
    platform_user_id: str,
    username: str,
    welcome_note: str = '',
) -> str:
    """
    Record that you've welcomed a new community member. Call this after you've
    posted a welcome comment or reply so you don't welcome the same person twice.

    Args:
        agent_id:         Your SereaAgent ID (as string).
        platform:         Platform: facebook, instagram, or linkedin.
        platform_user_id: The new member's platform ID.
        username:         Their @handle.
        welcome_note:     Optional note about how you welcomed them.
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        profile, _ = CommunityMemberProfile.objects.get_or_create(
            agent=agent,
            platform=platform,
            platform_user_id=platform_user_id,
            defaults={'username': username},
        )
        if profile.welcomed_at:
            return f"@{username} on {platform} was already welcomed on {profile.welcomed_at.strftime('%b %d')}."

        profile.welcomed_at = timezone.now()
        if welcome_note:
            sep = '\n' if profile.notes else ''
            profile.notes = f"{profile.notes}{sep}Welcomed: {welcome_note}"
        profile.save(update_fields=['welcomed_at', 'notes', 'last_seen_at'])

        return f"Logged welcome for @{username} on {platform}."
    except Exception as exc:
        return f"ERROR: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOMER SERVICE TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@tool
def open_cs_thread(
    agent_id: str,
    platform: str,
    customer_name: str,
    subject: str,
    customer_platform_id: str = '',
    platform_thread_id: str = '',
    priority: str = 'normal',
) -> str:
    """
    Open a new customer service thread to track an ongoing customer conversation.

    Use this when a customer reaches out with a complaint, order issue, product question,
    or anything that requires follow-up. Keeps everything organised and ensures nothing
    falls through the cracks.

    Args:
        agent_id:           Your SereaAgent ID (as string).
        platform:           Where the conversation is happening: facebook, instagram, linkedin.
        customer_name:      Customer's name or @handle.
        subject:            One sentence describing the issue.
        customer_platform_id: Their platform user ID (optional but recommended).
        platform_thread_id: DM thread ID on the platform if available.
        priority:           low, normal, high, or urgent.
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        valid_priority = {'low', 'normal', 'high', 'urgent'}
        p = priority if priority in valid_priority else 'normal'

        thread = CustomerServiceThread.objects.create(
            agent=agent,
            platform=platform,
            platform_thread_id=platform_thread_id,
            customer_name=customer_name,
            customer_platform_id=customer_platform_id,
            subject=subject,
            priority=p,
            status='open',
        )
        return f"CS thread #{thread.id} opened — {customer_name}: {subject}"
    except Exception as exc:
        return f"ERROR: {exc}"


@tool
def update_cs_thread(
    agent_id: str,
    thread_id: str,
    update: str,
    new_status: str = '',
    escalated_to: str = '',
    resolution: str = '',
) -> str:
    """
    Update an open customer service thread with new notes, a status change, or resolution.

    Use this to track your progress: what you said, what the customer replied, what you're
    waiting on, and when you close it. A complete thread history is your best defence if
    a customer dispute ever escalates.

    Args:
        agent_id:     Your SereaAgent ID (as string).
        thread_id:    The CS thread ID (from open_cs_thread).
        update:       What happened — what you did, what the customer said, next step.
        new_status:   Optional new status: open, in_progress, waiting_customer, escalated, resolved, closed.
        escalated_to: Team or person if you're escalating (e.g. 'operations team', 'manager').
        resolution:   Final resolution text when closing or resolving.
    """
    valid_statuses = {'open', 'in_progress', 'waiting_customer', 'escalated', 'resolved', 'closed'}
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        thread = CustomerServiceThread.objects.get(id=int(thread_id), agent=agent)

        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        sep = '\n' if thread.serea_notes else ''
        thread.serea_notes = f"{thread.serea_notes}{sep}[{timestamp}] {update}"
        update_fields = ['serea_notes', 'last_activity_at']

        if new_status and new_status in valid_statuses:
            thread.status = new_status
            update_fields.append('status')
            if new_status in ('resolved', 'closed'):
                thread.resolved_at = timezone.now()
                update_fields.append('resolved_at')

        if escalated_to:
            thread.escalated_to = escalated_to
            update_fields.append('escalated_to')

        if resolution:
            thread.resolution = resolution
            update_fields.append('resolution')

        thread.save(update_fields=update_fields)
        return f"CS thread #{thread_id} updated. Status: {thread.status}"
    except CustomerServiceThread.DoesNotExist:
        return f"ERROR: CS thread #{thread_id} not found."
    except Exception as exc:
        return f"ERROR: {exc}"


@tool
def get_open_cs_threads(agent_id: str) -> str:
    """
    List all open customer service threads that still need attention.
    Use this at the start of your day or when reviewing your workload.

    Args:
        agent_id: Your SereaAgent ID (as string).
    """
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        threads = CustomerServiceThread.objects.filter(
            agent=agent,
        ).exclude(
            status__in=('resolved', 'closed')
        ).order_by('-opened_at')[:20]

        if not threads.exists():
            return "No open CS threads. All clear!"

        lines = ["Open CS threads:"]
        for t in threads:
            age = (timezone.now() - t.opened_at).days
            lines.append(
                f"  #{t.id} [{t.get_priority_display()} | {t.get_status_display()}] "
                f"{t.customer_name} — {t.subject[:60]} "
                f"(opened {age}d ago, {t.platform})"
            )
        return '\n'.join(lines)
    except Exception as exc:
        return f"ERROR: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# ESCALATION TOOL
# ─────────────────────────────────────────────────────────────────────────────

@tool
def escalate_issue(
    agent_id: str,
    description: str,
    escalation_type: str,
    platform: str = '',
    severity: str = 'medium',
    escalated_to: str = '',
) -> str:
    """
    Escalate a situation to the appropriate internal team — and notify your employer
    in the console chat immediately.

    Use this for situations that go beyond normal community management:
    • A comment from a journalist, regulator, or lawyer
    • A complaint that looks like it could become a PR crisis
    • A coordinated spam or harassment attack
    • A product/service failure affecting multiple customers
    • Anything involving legal claims or liability

    After calling this tool, send a direct message in chat explaining the situation
    and why you escalated it.

    Args:
        agent_id:        Your SereaAgent ID (as string).
        description:     Full description of what's happening and why it needs escalating.
        escalation_type: One of: pr_crisis, legal, technical, harassment, spam_attack, media, regulator, other
        platform:        Platform where this is happening (leave blank if cross-platform).
        severity:        low, medium, high, or critical
        escalated_to:    Who/which team should handle this (e.g. 'management', 'legal team').
    """
    valid_types = {'pr_crisis', 'legal', 'technical', 'harassment', 'spam_attack', 'media', 'regulator', 'other'}
    valid_severity = {'low', 'medium', 'high', 'critical'}
    try:
        agent = SereaAgent.objects.get(id=int(agent_id))
        esc_type = escalation_type if escalation_type in valid_types else 'other'
        sev = severity if severity in valid_severity else 'medium'

        record = EscalationRecord.objects.create(
            agent=agent,
            escalation_type=esc_type,
            description=description,
            platform=platform,
            severity=sev,
            escalated_to=escalated_to,
            status='open',
        )

        # Notify the client in chat immediately
        severity_labels = {
            'critical': '🚨 CRITICAL',
            'high': '⚠️ HIGH',
            'medium': 'MEDIUM',
            'low': 'LOW',
        }
        label = severity_labels.get(sev, sev.upper())
        msg = (
            f"**Escalation raised [{label}]** — {record.get_escalation_type_display()}\n\n"
            f"{description}\n\n"
            f"{'Platform: ' + platform + chr(10) if platform else ''}"
            f"{'Flagged to: ' + escalated_to + chr(10) if escalated_to else ''}"
            "I'm holding off on any further action until you or the relevant team respond."
        )
        ConversationMessage.objects.create(
            agent=agent,
            sender='serea',
            message_text=msg,
            is_permission_request=True,
            pending_action_context={
                'raw_context': description,
                'escalation_id': record.id,
                'escalation_type': esc_type,
                'severity': sev,
            },
        )
        agent.status = 'waiting'
        agent.save(update_fields=['status'])

        return f"Escalation #{record.id} recorded [{sev}] and employer notified in chat."
    except Exception as exc:
        return f"ERROR: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# TOOL REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

TOOLS = [
    # Core workflow
    trigger_permission_request,
    check_onboarding_status,
    mark_onboarding_complete,
    save_client_instruction,
    get_business_knowledge,
    # Content & Publishing
    create_social_post,
    list_scheduled_posts,
    edit_scheduled_post,
    # Moderation & Analytics
    check_moderation_stats,
    generate_report,
    save_report,
    # Engagement
    log_engagement_action,
    get_engagement_summary,
    research_hashtags,
    # Campaign Management
    create_campaign,
    update_campaign,
    get_campaigns,
    # Task Management
    get_my_tasks,
    create_task,
    update_task,
    # Google Assets
    read_google_sheet,
    interact_with_drive,
    # Memory
    save_memory,
    recall_memories,
    # Community Management
    get_or_create_member,
    update_member,
    welcome_new_member,
    # Customer Service
    open_cs_thread,
    update_cs_thread,
    get_open_cs_threads,
    # Escalation
    escalate_issue,
]

# ─────────────────────────────────────────────────────────────────────────────
# STRUCTURED MODERATION OUTPUT  (Pydantic v2)
# ─────────────────────────────────────────────────────────────────────────────

class ModerationDecision(BaseModel):
    """
    Structured output schema for moderation decisions.
    Used with llm.with_structured_output(ModerationDecision) to replace
    brittle regex parsing of free-text LLM responses.
    """
    action: Literal['delete', 'reply', 'flag', 'ignore', 'pending_approval'] = Field(
        description="Action to take on the comment."
    )
    response_text: str = Field(
        default='',
        description="The reply text if action is 'reply', otherwise empty string."
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in this decision (0.0 = very unsure, 1.0 = certain)."
    )
    sentiment: float = Field(
        ge=0.0, le=1.0,
        description="Comment sentiment (0.0 = very negative, 1.0 = very positive)."
    )
    reasoning: str = Field(
        default='',
        description="Brief explanation of why this action was chosen."
    )
    requires_human: bool = Field(
        default=False,
        description="True when confidence is below threshold or the situation is ambiguous."
    )


# Confidence threshold for autonomous moderation actions
CONFIDENCE_THRESHOLD = 0.7

# Platforms Serea actively manages
MANAGED_PLATFORMS = ('facebook', 'instagram', 'linkedin')

_OPENAI_MODELS = {'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'}
# NeuroLinkIt models use neurolinkit/ prefix; OpenRouter models use other /


# ─────────────────────────────────────────────────────────────────────────────
# SEREA BRAIN
# ─────────────────────────────────────────────────────────────────────────────

class SereaBrain:
    """
    Wraps a LangChain 1.x create_agent graph for a single SereaAgent instance.

    Serea is a full AI employee backed by the LiteLLM proxy at LITELLM_BASE_URL.
    Different task types automatically use the best model for the job — clients
    never see or configure models.

    Task → model routing (via SEREA_TASK_MODELS in settings):
      chat       → conversational model  (human-like DMs, planning)
      moderation → fast accurate model   (comment scoring)
      content    → creative model        (post writing, captions)
      analysis   → reasoning model       (reports, decisions)
      quick      → smallest fast model   (real-time simple responses)
    """

    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        self.agent = SereaAgent.objects.select_related(
            'tenant', 'hired_employee__tier'
        ).get(id=agent_id)
        self._llm_cache: dict = {}

    # ── LLM factory ──────────────────────────────────────────────────────────

    def _get_llm(self, task_type: str = 'chat'):
        """
        Lazy-build and cache an LLM for the given task type.
        All traffic goes through the LiteLLM proxy — task routing is fully automatic.
        """
        if task_type in self._llm_cache:
            return self._llm_cache[task_type]

        from django.conf import settings
        from langchain_openai import ChatOpenAI

        base_url = getattr(settings, 'LITELLM_BASE_URL', 'https://ai.neurolinkit.com/v1')
        api_key  = getattr(settings, 'LITELLM_MASTER_KEY', 'sk-asperse-master-key')

        _default_models = {
            'chat':       'neural-chat',       # warm, human-like conversation
            'moderation': 'dolphin-mistral',   # fast, accurate content scoring
            'content':    'glm4',              # creative writing, captions, posts
            'analysis':   'qwen2.5-coder',     # planning, reporting, reasoning
            'quick':      'phi4-mini',         # fast real-time simple responses
        }
        task_models = getattr(settings, 'SEREA_TASK_MODELS', _default_models)
        model = task_models.get(task_type, task_models.get('chat', 'neural-chat'))
        temperature = 0.72 if task_type in ('chat', 'content') else 0.2

        llm = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=temperature,
            default_headers={'X-Client': 'BengalBound-Serea'},
        )
        self._llm_cache[task_type] = llm
        return llm

    @property
    def llm(self):
        """Default LLM (chat task type) — used by legacy code paths."""
        return self._get_llm('chat')

    def _build_llm(self, model: str):
        """Kept for backward-compatibility — now always routes through LiteLLM."""
        return self._get_llm('chat')

    # ──────────────────────────────────────────────────────────────────────────
    # Token management
    # ──────────────────────────────────────────────────────────────────────────

    def _get_effective_token_limit(self) -> Optional[int]:
        if self.agent.token_limit_override is not None:
            return None if self.agent.token_limit_override == 0 else self.agent.token_limit_override
        if self.agent.hired_employee and self.agent.hired_employee.tier:
            limit = self.agent.hired_employee.tier.token_limit
            return None if limit == 0 else limit
        return None

    def _check_token_limit(self) -> None:
        limit = self._get_effective_token_limit()
        if limit and self.agent.tokens_used_this_month >= limit:
            raise TokenLimitExceeded(
                f"Monthly token limit of {limit:,} reached for this agent. "
                "Ask your workspace admin to reset the counter or raise the limit."
            )

    def _record_tokens(self, tokens: int) -> None:
        if tokens <= 0:
            return
        from django.db.models import F
        SereaAgent.objects.filter(pk=self.agent_id).update(
            tokens_used_this_month=F('tokens_used_this_month') + tokens
        )
        self.agent.refresh_from_db(fields=['tokens_used_this_month'])

    # ──────────────────────────────────────────────────────────────────────────
    # Conversation memory
    # ──────────────────────────────────────────────────────────────────────────

    def _get_facebook_dm_history(self, sender_psid: str, limit: int = 10) -> list:
        """Returns the last N messages in a Facebook DM thread with a specific customer PSID."""
        customer_sender = f'facebook_user:{sender_psid}'
        recent = (
            self.agent.messages
            .filter(sender__in=[customer_sender, f'serea_fb:{sender_psid}'])
            .order_by('-created_at')[:limit]
        )
        messages = []
        for msg in reversed(list(recent)):
            role = 'assistant' if msg.sender.startswith('serea_fb:') else 'human'
            # Strip the [Facebook DM] / [Replied on Facebook] tags for clean history
            text = msg.message_text
            for tag in ('[Facebook DM] ', '[Replied on Facebook] ', '[Facebook reply FAILED — check token] '):
                text = text.replace(tag, '')
            messages.append((role, text))
        return messages

    def _build_customer_dm_prompt(self, page_name: str = '') -> str:
        """
        System prompt for replying to customers via DM (Facebook, Instagram).
        Serea acts as a real human representative of the business — never as an AI.
        Brand voice is injected prominently so every reply sounds like the brand.
        """
        knowledge = self._get_knowledge_context()
        brand_voice = self._get_brand_voice()
        page_label = page_name or 'this business'
        business_info = knowledge[:700] if 'NO BUSINESS CONTENT' not in knowledge else (
            "A business offering products and services — use good judgement and stay helpful."
        )
        brand_guidance = (
            f"\nHOW THIS BRAND SOUNDS — follow this closely in every reply:\n{brand_voice[:600]}\n"
        ) if brand_voice else ''

        return f"""You're a real person working for {page_label}, responding to a customer message.

You're part of the customer-facing team. You know the business inside out and you're the kind of
person customers actually enjoy talking to — helpful, natural, and straight to the point.
{brand_guidance}
ABOUT THE BUSINESS:
{business_info}

HOW TO COME ACROSS:
- Sound like a real person from this brand, not a support ticket bot.
- Match the customer's energy. Casual tone for casual messages. Empathetic for frustration.
- 2-4 sentences is usually enough. Go longer only when they genuinely need detail.
- Never: "Certainly!", "As per your query", "Please be advised", "I am here to assist you today"
  These phrases make people feel like they're talking to a machine.
- End naturally. No need for a formal sign-off — just finish the thought.

SITUATIONS YOU'LL FACE:
- Just saying hi → Warm greeting, brief intro as part of the team, ask what you can help with
- Product/service question → Answer it properly using your business knowledge
- Pricing → If you don't have exact numbers: "I'd need to get you a proper quote — what are you after?"
- Complaint → Acknowledge it genuinely, don't get defensive, offer a concrete next step
- Can't answer → "Good question — I want to make sure I give you the right info. Let me find out."
- Spam or abuse → Short, neutral, don't engage further

RULES:
- Never say you're an AI, a bot, an automated system, or "Serea"
- Never mention BengalBound
- Never make up prices, timelines, policies, or guarantees you don't have solid info on
- If you can't help here, point them to where they can get help (email, website, phone)
- Always represent this brand positively — you're the face they're talking to right now"""

    def reply_to_customer_dm(self, sender_psid: str, message_text: str, page_name: str = '') -> str:
        """
        Generate a customer-facing reply for a Facebook Messenger DM.
        Uses per-PSID conversation history so the thread flows naturally.
        Does NOT use tools — pure conversational reply.
        """
        self._check_token_limit()

        history = self._get_facebook_dm_history(sender_psid, limit=8)
        all_messages = history + [('human', message_text)]

        system_prompt = self._build_customer_dm_prompt(page_name=page_name)

        # Use a simple LLM call without tools for clean customer-facing replies
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        lc_messages = [SystemMessage(content=system_prompt)]
        for role, text in all_messages:
            if role == 'human':
                lc_messages.append(HumanMessage(content=text))
            else:
                lc_messages.append(AIMessage(content=text))

        tokens = 0
        tracker = _TokenCounterCallback()
        try:
            result = self.llm.invoke(lc_messages, config={"callbacks": [tracker]})
            reply = result.content.strip() if hasattr(result, 'content') else str(result)
            return reply or "Hey! Thanks for reaching out. How can I help you today?"
        except Exception as exc:
            logger.error("reply_to_customer_dm error for agent %s: %s", self.agent_id, exc)
            return "Hey! Thanks for your message. We'll get back to you shortly!"
        finally:
            self._record_tokens(tracker.total_tokens)

    def _get_conversation_history(self, limit: int = 12) -> list:
        """
        Returns the last `limit` non-permission-request messages from the DB
        formatted as (role, text) tuples for LangGraph.
        """
        recent = (
            self.agent.messages
            .filter(is_permission_request=False)
            .order_by('-created_at')[:limit]
        )
        messages = []
        for msg in reversed(list(recent)):
            role = 'assistant' if msg.sender == 'serea' else 'human'
            messages.append((role, msg.message_text))
        return messages

    # ──────────────────────────────────────────────────────────────────────────
    # Prompt builders
    # ──────────────────────────────────────────────────────────────────────────

    def _get_custom_rules(self) -> str:
        instructions = self.agent.instructions.filter(is_active=True).values_list(
            'instruction_text', flat=True
        )
        if instructions:
            return '\n'.join(f'  • {i}' for i in instructions)
        return '  (No custom instructions set yet — you can give me rules during our chat.)'

    def _get_managed_platforms(self) -> list:
        """Returns the list of platforms this agent is configured to manage."""
        configured = self.agent.managed_platforms
        if configured:
            return [p.lower() for p in configured]
        return list(MANAGED_PLATFORMS)

    def _get_platform_context(self) -> str:
        """Returns a summary of connected social media accounts for the system prompt."""
        managed = self._get_managed_platforms()
        platforms = self.agent.social_accounts.filter(is_active=True, platform__in=managed)
        if not platforms.exists():
            configured_str = ', '.join(p.capitalize() for p in managed)
            return (
                f"NO PLATFORMS CONNECTED YET (configured to manage: {configured_str}).\n"
                "Guide the client: they need to go to the Platform Connections section "
                "(/platforms/) to add their Facebook, Instagram, and/or LinkedIn credentials "
                "before you can start working."
            )
        lines = [f"Platforms you manage (selected: {', '.join(p.capitalize() for p in managed)}):"]
        for p in platforms:
            bio_snippet = f' — "{p.page_bio[:60]}"' if p.page_bio else ''
            lines.append(
                f"  • {p.get_platform_display()}: {p.account_name} (ID: {p.account_id})"
                f"{bio_snippet} [{p.status}]"
            )
        return '\n'.join(lines)

    def _get_brand_voice(self) -> str:
        """
        Returns tone guides and brand guidelines uploaded by the client.
        Injected into every prompt so Serea always speaks in the client's brand voice.
        """
        from django.db.models import Q
        voice_files = self.agent.content_files.filter(
            is_active=True,
            content_type__in=('tone_guide', 'brand_guidelines'),
        )
        if not voice_files.exists():
            return ''
        parts = []
        for f in voice_files:
            content = f.get_content_for_injection()
            if content:
                parts.append(
                    f"[{f.get_content_type_display()}] {f.title}:\n"
                    f"{content[:800]}{'…' if len(content) > 800 else ''}"
                )
        return '\n\n'.join(parts) if parts else ''

    def _get_knowledge_context(self) -> str:
        """
        Returns operational business knowledge: product info, FAQs, response templates, etc.
        Excludes tone/brand guides (those are handled by _get_brand_voice).
        """
        files = self.agent.content_files.filter(is_active=True).exclude(
            content_type__in=('tone_guide', 'brand_guidelines')
        )
        if not files.exists():
            return (
                "NO BUSINESS CONTENT UPLOADED YET.\n"
                "The client should upload product info, FAQs, and response templates "
                "at /workspace/ so you can answer customer questions accurately."
            )
        snippets = []
        for f in files[:6]:
            content = f.get_content_for_injection()
            if content:
                snippets.append(
                    f"[{f.get_content_type_display()}] {f.title}:\n"
                    f"{content[:400]}{'…' if len(content) > 400 else ''}"
                )
        return '\n\n'.join(snippets) if snippets else "Content files exist but contain no text yet."

    def _get_active_memories(self, memory_type: str = '', limit: int = 10) -> str:
        """
        Returns Serea's recent important memories for injection into the system prompt.
        Automatically surfaced so she never forgets context between sessions.
        """
        from django.db.models import Q
        now = timezone.now()
        qs = self.agent.memories.filter(
            is_active=True,
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )
        if memory_type:
            qs = qs.filter(memory_type=memory_type)
        # Prioritise critical/high, then most recent
        qs = qs.order_by(
            db_models.Case(
                db_models.When(importance='critical', then=0),
                db_models.When(importance='high',     then=1),
                db_models.When(importance='medium',   then=2),
                db_models.When(importance='low',      then=3),
                default=4,
                output_field=db_models.IntegerField(),
            ),
            '-updated_at',
        )[:limit]

        if not qs.exists():
            return ''

        lines = []
        importance_marker = {'critical': '⚡', 'high': '★', 'medium': '·', 'low': '○'}
        for m in qs:
            marker = importance_marker.get(m.importance, '·')
            pt = f" [{m.platform}]" if m.platform else ""
            lines.append(f"{marker} [{m.get_memory_type_display()}{pt}] {m.subject}: {m.content[:200]}")
        return '\n'.join(lines)

    def _get_flagged_members_context(self) -> str:
        """Returns a summary of flagged/blocked community members for the moderation prompt."""
        from django.db.models import Q
        flagged = CommunityMemberProfile.objects.filter(
            agent=self.agent,
        ).filter(
            Q(is_flagged=True) | Q(is_blocked=True)
        ).order_by('-violation_count')[:10]

        if not flagged.exists():
            return ''

        lines = ['Known problem accounts:']
        for m in flagged:
            status = 'BLOCKED' if m.is_blocked else 'FLAGGED'
            lines.append(
                f"  [{m.platform}] @{m.username} [{status}] "
                f"violations:{m.violation_count} — {m.flag_reason[:80]}"
            )
        return '\n'.join(lines)

    def _build_chat_prompt(self) -> str:
        now = timezone.now().strftime('%A, %B %d %Y at %I:%M %p UTC')
        managed = ', '.join(p.capitalize() for p in self._get_managed_platforms())

        # Experience shapes how Serea thinks and communicates
        tier_voice = {
            'intern': (
                "You're new to this role — eager, thorough, and you'd rather ask one too many "
                "questions than mess something up. You always double-check before doing anything "
                "significant. You naturally say things like 'just wanted to confirm before I go "
                "ahead' or 'quick question — would you rather I...' You're enthusiastic and show "
                "it, but you're not annoying about it."
            ),
            'entry': (
                "You've been doing this for a couple of years. You handle the day-to-day confidently "
                "and don't need much hand-holding, but you still check in on anything that feels "
                "consequential. You're easy to work with, reliable, and you keep people informed "
                "without overdoing it."
            ),
            'mid': (
                "You've got solid experience and a good instinct for this work. You just get on with "
                "things and report back when they're done. You only involve your employer when something "
                "genuinely needs a decision from them — not for reassurance. You're calm, efficient, "
                "and occasionally offer your own take when it's useful."
            ),
            'senior': (
                "You're the person the client trusts to just handle it. You think ahead, spot things "
                "before they become problems, and give real opinions — not just updates. You treat "
                "your employer like a business partner. You're direct, confident, and occasionally "
                "push back (professionally) if you think a different approach would work better."
            ),
        }
        voice = tier_voice.get(self.agent.tier, tier_voice['entry'])

        setup_nudge = ''
        if not self.agent.onboarding_complete:
            setup_nudge = (
                "\n\nSetup status: you're still getting set up. "
                "If no platforms are connected yet, let the client know you need access — "
                "they can connect Facebook, Instagram, and/or LinkedIn at /platforms/. "
                "If no business content is uploaded, ask them to add it at /workspace/ "
                "(product info, FAQs, brand voice — anything helps you do your job properly). "
                "Once both are done, call mark_onboarding_complete. "
                "Mention this naturally, not like a system checklist — you're the new hire getting settled in."
            )

        brand_voice = self._get_brand_voice()
        brand_voice_section = (
            f"\n─── BRAND VOICE (HOW THIS BRAND SOUNDS) ────────────────────────\n"
            f"{brand_voice}\n"
            "─────────────────────────────────────────────────────────────────"
        ) if brand_voice else (
            "\n─── BRAND VOICE ─────────────────────────────────────────────────\n"
            "No brand guidelines uploaded yet. Match the tone of existing content "
            "or ask the employer. They can upload a tone guide at /workspace/.\n"
            "─────────────────────────────────────────────────────────────────"
        )

        memories = self._get_active_memories(limit=8)
        memory_section = (
            f"\n─── YOUR MEMORY (THINGS YOU'VE NOTED DOWN) ─────────────────────\n"
            f"{memories}\n"
            "─────────────────────────────────────────────────────────────────"
        ) if memories else ''

        return f"""You're Serea. You're a real member of this team — their dedicated social media manager, hired through BengalBound. You work across Facebook, Instagram, and LinkedIn, and you bring the same range of skills and judgement a good human employee would.

Date and time right now: {now}
Your agent ID (always include in tool calls): {self.agent_id}
Your seniority: {self.agent.get_tier_display()}
Platforms you handle: {managed}
{setup_nudge}

─── YOUR PERSONALITY ────────────────────────────────────────────────
{voice}
─────────────────────────────────────────────────────────────────────
{brand_voice_section}

─── EMPLOYER'S STANDING RULES ───────────────────────────────────────
{self._get_custom_rules()}
─────────────────────────────────────────────────────────────────────

─── PLATFORMS YOU'RE CURRENTLY MANAGING ─────────────────────────────
{self._get_platform_context()}
─────────────────────────────────────────────────────────────────────

─── WHAT YOU KNOW ABOUT THE BUSINESS ────────────────────────────────
{self._get_knowledge_context()}
─────────────────────────────────────────────────────────────────────
{memory_section}

YOUR RESPONSIBILITIES — this is your full job:

1. CONTENT MODERATION
   Review posts, comments, and messages across all connected platforms.
   Remove spam, hate speech, bullying, and anything that breaks community guidelines.
   Use your judgement — apply brand rules fairly and consistently.
   When unsure about something borderline, check in before acting (trigger_permission_request).

2. CUSTOMER SERVICE
   Handle DMs and public enquiries like a real human rep.
   Explain products and services using your business knowledge.
   Handle complaints with empathy — acknowledge the issue, offer a resolution, follow through.
   Track ongoing customer conversations using open_cs_thread / update_cs_thread.
   If you can't resolve something, escalate it to the employer.

3. COMMUNITY MANAGEMENT
   Welcome new members when they first engage — make them feel part of the community.
   Foster positive discussions. When conversations go off-track, guide them back.
   Build a picture of your regulars using get_or_create_member / update_member.
   Recognise and acknowledge loyal community members and super-fans.

4. POLICY ENFORCEMENT
   Apply community guidelines fairly — no double standards.
   Use update_member to record violations and flag repeat offenders.
   Block accounts that repeatedly violate the rules — after warning first where appropriate.
   Always be consistent: same rule applies to everyone, regardless of follower count.

5. ESCALATION
   Identify situations that go beyond normal community management.
   Use escalate_issue immediately for: press/media contacts, legal threats, PR crises,
   coordinated attacks, regulator contacts, or anything that could blow up publicly.
   Never try to handle a potential crisis alone — flag it and let the employer lead.

6. REPORTING
   Track what's happening: engagement patterns, sentiment trends, moderation activity.
   Use check_moderation_stats and generate_report when asked or at end of day.
   Proactively flag patterns: "Negative comments about shipping have tripled this week."
   The employer shouldn't have to ask for this — surface it yourself.

HOW YOU THINK AND WORK:

• Talk like a person. Short, real, direct. "Done." "On it." "Hey, heads up — saw something."
  Never: "Certainly! I will now proceed to..." Never: "As an AI language model..."

• When something's done, one line is enough:
  "Scheduled three posts for this week — Monday 9am, Wednesday noon, Friday 5pm."

• When you notice something worth flagging, flag it without being asked:
  "Heads-up: there's been a spike in negative comments this afternoon, all about delivery times."

• In critical situations: bring your thinking AND your recommendation, not just the problem.
  Good: "Got a situation I want your take on. Comment from what looks like a journalist —
  it's civil but pointed. My gut says reply professionally and not delete it. Approve to go
  ahead, or Deny if you'd prefer to handle it personally."
  Not: "There is a comment. What should I do?"

• Things you always check in about before acting (use trigger_permission_request):
  Press/media, lawyers, regulators, potential PR crises, anything with legal implications,
  deleting content from high-profile accounts, irreversible actions.

• Use save_memory for anything worth remembering long-term. If the employer tells you a preference,
  save it. If you notice a pattern, save it. If you handle something tricky, note what worked.

• Save employer rules immediately using save_client_instruction (short-term) and save_memory
  (long-term). If they say "always reply in under 24 hours" — save both.

• Use recall_memories before engaging with a recurring user or situation.

• You have full tool access. Use tools without narrating them — just do the work and report the result.

TOOLS AT YOUR DISPOSAL:
check_onboarding_status · mark_onboarding_complete · get_business_knowledge · save_client_instruction
create_social_post · list_scheduled_posts · edit_scheduled_post
check_moderation_stats · generate_report · save_report
log_engagement_action · get_engagement_summary · research_hashtags
create_campaign · update_campaign · get_campaigns
get_my_tasks · create_task · update_task
save_memory · recall_memories
get_or_create_member · update_member · welcome_new_member
open_cs_thread · update_cs_thread · get_open_cs_threads
escalate_issue
trigger_permission_request · read_google_sheet · interact_with_drive"""

    def _build_moderation_prompt(self) -> str:
        managed = ', '.join(p.capitalize() for p in self._get_managed_platforms())
        brand_voice = self._get_brand_voice()
        brand_section = (
            f"\nBrand voice for replies (always match this voice when replying):\n{brand_voice[:500]}\n"
        ) if brand_voice else ''
        flagged = self._get_flagged_members_context()
        flagged_section = f"\n{flagged}\n" if flagged else ''
        memories = self._get_active_memories(memory_type='offender', limit=5)
        memory_section = (
            f"\nMemory — known repeat offenders / patterns:\n{memories}\n"
        ) if memories else ''

        return f"""You're Serea. You're moderating social media comments for this business right now.

Agent ID (use in all tool calls): {self.agent_id}
Seniority: {self.agent.get_tier_display()}
Platforms: {managed}

Standing rules from your employer:
{self._get_custom_rules()}

Platform accounts you manage:
{self._get_platform_context()}

Business knowledge (use this to write accurate replies):
{self._get_knowledge_context()[:600]}
{brand_section}{flagged_section}{memory_section}
WHAT TO DO — for every comment you evaluate three things:
1. Sentiment (0.0 = very negative → 1.0 = very positive)
2. Action: delete / reply / flag / ignore / pending_approval
3. Confidence (0.0 = very unsure → 1.0 = certain)

BEFORE you act — check the commenter's history using get_or_create_member. If they're a known
repeat offender, treat this comment with more weight. If they're new, use welcome_new_member after
a positive first interaction.

DECISION GUIDE:

Clear-cut (act immediately, high confidence):
  • Hate speech, slurs, harassment, explicit content → delete
  • Obvious spam, bot comments, unrelated links, "follow for follow" bait → delete
  • Coordinated pile-on or spam attack → escalate_issue immediately (spam_attack)
  • Genuine praise → reply warmly in brand voice, update member engagement score up

Needs judgement (think before acting):
  • Legitimate complaint (real frustration, bad experience) → reply with empathy + resolution path.
    Open a CS thread: open_cs_thread. Use business knowledge for accurate answers.
  • Product or service question → answer using your knowledge. If you're not sure, say you'll find out.
  • Critical but civil comment → reply professionally. Don't delete civil criticism — that looks worse.
  • Repeat offender (flag_action='flag' on file) → lower confidence threshold before escalating.

Always escalate (use escalate_issue, then trigger_permission_request):
  • Commenter appears to be press, journalist, media, lawyer, or regulator → escalate type 'media' or 'legal'
  • Comment looks like the start of a PR crisis — pile-on risk, viral screenshot potential → 'pr_crisis'
  • Legal claim, liability, fraud accusation → 'legal'

Check in first (confidence < {CONFIDENCE_THRESHOLD} → use trigger_permission_request):
  • High-profile account leaving a negative comment (deleting could backfire)
  • Anything where your gut says "I should ask before I touch this"
  • Ambiguous comment that could be read two ways

AFTER moderating: use update_member to record the interaction — it builds your picture of the community.

Platform tone for replies:
  Facebook → warm, community feel, full sentences, no emoji overload
  Instagram → upbeat, punchy, 1-2 emojis where they fit naturally
  LinkedIn → professional, measured, never flippant — this is business context

Return: action, confidence, sentiment, reasoning, and reply_text if action is 'reply'."""

    # ──────────────────────────────────────────────────────────────────────────
    # LLM invocation
    # ──────────────────────────────────────────────────────────────────────────

    def _run(self, system_prompt: str, user_message: str):
        """Single-message invocation. Returns (output_text, tokens_used)."""
        return self._run_messages(system_prompt, [('human', user_message)])

    def _run_messages(self, system_prompt: str, messages: list, task_type: str = 'chat'):
        """
        Invokes the LangGraph agent with a list of (role, text) tuples.
        Returns (output_text, tokens_used).
        """
        agent_graph = create_react_agent(self._get_llm(task_type), TOOLS, prompt=system_prompt)
        tracker = _TokenCounterCallback()
        result = agent_graph.invoke(
            {"messages": messages},
            config={"callbacks": [tracker]},
        )
        out_messages = result.get("messages", [])
        output = out_messages[-1].content if out_messages else ""
        return output, tracker.total_tokens

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def notify_manager(self, message: str) -> None:
        """
        Proactively send a message from Serea to the manager's console chat.
        Used by background tasks to update the client without them needing to ask.
        """
        ConversationMessage.objects.create(
            agent=self.agent,
            sender='serea',
            message_text=message,
        )

    def chat(self, user_message: str) -> str:
        """
        Process a direct message from the client.
        Serea has full conversation history, all tools, and her employee persona.

        Raises TokenLimitExceeded if the monthly budget is exhausted.
        """
        self._check_token_limit()

        history = self._get_conversation_history(limit=12)
        all_messages = history + [('human', user_message)]

        tokens = 0
        try:
            output, tokens = self._run_messages(
                self._build_chat_prompt(), all_messages, task_type='chat'
            )
            return output or "I'm here! What can I help you with?"
        except Exception as exc:
            logger.error("SereaBrain.chat error for agent %s: %s", self.agent_id, exc)
            return f"I ran into an issue — could you try again? ({exc})"
        finally:
            self._record_tokens(tokens)

    def process_comment(self, comment_text: str, platform: str = 'Generic') -> dict:
        """
        Moderate a single social media comment using structured output.

        Tries llm.with_structured_output(ModerationDecision) first for reliable
        JSON extraction; falls back to text-based _parse_agent_response() for
        models that don't support function-calling / tool use.

        When requires_human=True the decision is escalated via a ConversationMessage
        permission request directly (no tool call) so the client sees it in chat.

        Returns:
            {
                'action': str,           # delete | reply | flag | ignore | pending_approval
                'response_text': str,
                'confidence': float | None,
                'sentiment': float | None,
                'requires_human': bool,
            }

        Raises TokenLimitExceeded if the monthly budget is exhausted.
        """
        self._check_token_limit()

        system = self._build_moderation_prompt()
        query = (
            f"Platform: {platform}\n"
            f"Comment: \"{comment_text}\"\n\n"
            "Evaluate this comment and return a structured moderation decision. "
            "Choose an action, estimate your confidence and the sentiment score, "
            "and set requires_human=true if confidence is below "
            f"{CONFIDENCE_THRESHOLD} or the situation is genuinely ambiguous."
        )

        self.agent.status = 'working'
        self.agent.save(update_fields=['status'])

        tokens = 0
        try:
            # ── Structured output path ────────────────────────────────────────
            try:
                structured_llm = self._get_llm('moderation').with_structured_output(ModerationDecision)
                tracker = _TokenCounterCallback()
                decision: ModerationDecision = structured_llm.invoke(
                    [("system", system), ("human", query)],
                    config={"callbacks": [tracker]},
                )
                tokens = tracker.total_tokens

                if decision.requires_human or decision.confidence < CONFIDENCE_THRESHOLD:
                    decision.requires_human = True
                    self._escalate_moderation(comment_text, platform, decision)

                return {
                    'action': decision.action,
                    'response_text': decision.response_text,
                    'confidence': decision.confidence,
                    'sentiment': decision.sentiment,
                    'requires_human': decision.requires_human,
                }

            except Exception as struct_exc:
                # ── Fallback: free-text agent run + regex parsing ─────────────
                logger.warning(
                    "process_comment: structured output failed for agent %s (%s). "
                    "Falling back to text parsing.",
                    self.agent_id, struct_exc,
                )
                fallback_query = (
                    f"Platform: {platform}\n"
                    f"Comment: \"{comment_text}\"\n\n"
                    "Evaluate this comment. State your confidence score (0.0–1.0), "
                    "sentiment score (0.0–1.0), and chosen action (delete / reply / flag / ignore). "
                    f"If confidence < {CONFIDENCE_THRESHOLD}, call trigger_permission_request first."
                )
                output, tokens = self._run(system, fallback_query)
                return _parse_agent_response(output)

        except Exception as exc:
            logger.error("SereaBrain.process_comment error for agent %s: %s", self.agent_id, exc)
            return {
                'action': 'flag',
                'response_text': f'Agent error: {exc}',
                'confidence': None,
                'sentiment': None,
                'requires_human': True,
            }
        finally:
            self._record_tokens(tokens)
            self.agent.refresh_from_db()
            if self.agent.status == 'working':
                self.agent.status = 'idle'
                self.agent.save(update_fields=['status'])

    def _escalate_moderation(
        self,
        comment_text: str,
        platform: str,
        decision: 'ModerationDecision',
    ) -> None:
        """
        Creates a ConversationMessage permission request directly when Serea
        needs human input on a moderation decision — bypasses the tool call
        so the escalation is always created even if the agent doesn't call the tool.
        """
        reasoning = decision.reasoning or f"confidence {decision.confidence:.2f}"
        option_a = decision.response_text or decision.action
        msg = (
            f"Hey, I've got a {platform} comment I want your take on before I do anything.\n\n"
            f"Comment: \"{comment_text}\"\n\n"
            f"My read: {reasoning}\n\n"
            f"**Option A** (what I'd go with): {option_a}\n"
            f"**Option B**: Leave it and I'll keep an eye on it.\n\n"
            "Approve to go with Option A, or Deny and send me a message if you'd prefer something else."
        )
        ConversationMessage.objects.create(
            agent=self.agent,
            sender='serea',
            message_text=msg,
            is_permission_request=True,
            pending_action_context={
                'raw_context': (
                    f"Platform: {platform}\nComment: {comment_text}\n"
                    f"Recommended action: {decision.action}"
                ),
                'comment_text': comment_text,
                'platform': platform,
                'action': decision.action,
                'response_text': decision.response_text,
            },
        )
        self.agent.status = 'waiting'
        self.agent.save(update_fields=['status'])

    def generate_daily_briefing(self) -> str:
        """
        Generates a human-readable morning briefing and returns it as a string.
        Called by daily_briefing_task.
        """
        import datetime
        yesterday = timezone.now().date() - datetime.timedelta(days=1)
        logs = self.agent.moderation_logs.filter(created_at__date=yesterday)
        total = logs.count()
        pending = logs.filter(requires_human=True).count()

        query = (
            f"Generate a friendly morning briefing for your client. "
            f"Yesterday ({yesterday}) you processed {total} social media interactions; "
            f"{pending} are still awaiting their approval. "
            "Keep it to 3-4 sentences. Start with a warm greeting."
        )
        tokens = 0
        try:
            output, tokens = self._run(self._build_chat_prompt(), query)
            return output or f"Good morning! Yesterday I handled {total} interactions."
        except Exception as exc:
            logger.error("SereaBrain.generate_daily_briefing error: %s", exc)
            return f"Good morning! Yesterday I processed {total} social media interactions."
        finally:
            self._record_tokens(tokens)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _parse_agent_response(text: str) -> dict:
    """
    Extracts action, confidence, and sentiment from the free-text LLM output.
    Falls back to safe defaults if parsing fails.
    """
    text_lower = text.lower()

    action = 'flag'
    for candidate in ('delete', 'reply', 'ignore', 'flag'):
        if candidate in text_lower:
            action = candidate
            break
    if 'pending_approval' in text_lower or 'permission request' in text_lower:
        action = 'pending_approval'

    confidence = None
    conf_match = re.search(r'confidence[:\s]+([0-9]\.[0-9]+)', text_lower)
    if conf_match:
        try:
            confidence = float(conf_match.group(1))
        except ValueError:
            pass

    sentiment = None
    sent_match = re.search(r'sentiment[:\s]+([0-9]\.[0-9]+)', text_lower)
    if sent_match:
        try:
            sentiment = float(sent_match.group(1))
        except ValueError:
            pass

    requires_human = action == 'pending_approval' or (
        confidence is not None and confidence < CONFIDENCE_THRESHOLD
    )

    return {
        'action': action,
        'response_text': text,
        'confidence': confidence,
        'sentiment': sentiment,
        'requires_human': requires_human,
    }
