"""
serea/tasks.py
──────────────
Celery background tasks for the Serea AI Social Media Moderator.

Three recurring task types (configured in CELERY_BEAT_SCHEDULE in settings.py):
  1. monitor_social_task   — poll for new comments and moderate them
  2. execute_content_task  — post scheduled content from ContentQueue
  3. daily_briefing_task   — generate and post a morning summary to the chat

Human-in-the-Loop resumption:
  After a client approves a permission request, the `resume_after_approval` task
  is called from the console_admin AJAX endpoint to execute the pending action.
"""

import logging
from celery import shared_task
from django.utils import timezone

from .models import (
    SereaAgent, ContentQueue, ModerationLog, ConversationMessage,
    SocialMediaAccount, SereaTask, DailyReport, DailyReportItem,
)
from .logic import SereaBrain, _parse_agent_response, TokenLimitExceeded
from .platform_api import PlatformAPIError
from .platforms import get_adapter

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1. MODERATION MONITOR
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def monitor_social_task(self, agent_id: int):
    """
    Periodically checks for new social media comments and moderates them.
    Schedule: every 10 minutes via Celery Beat (see settings.py).

    In production, replace the `new_comments` stub with real API calls to
    Meta Graph API, Twitter/X API, etc., using credentials stored in AICredential.
    """
    logger.info("monitor_social_task started for agent_id=%s", agent_id)
    try:
        agent = SereaAgent.objects.get(id=agent_id)
    except SereaAgent.DoesNotExist:
        logger.error("monitor_social_task: SereaAgent %s not found.", agent_id)
        return

    if agent.status in ('offline', 'waiting'):
        logger.info("Skipping monitor_social_task: agent %s is %s.", agent_id, agent.status)
        return

    try:
        brain = SereaBrain(agent_id=agent_id)
    except (TokenLimitExceeded, ValueError) as exc:
        logger.warning("monitor_social_task aborted for agent %s: %s", agent_id, exc)
        ConversationMessage.objects.create(agent=agent, sender='serea', message_text=str(exc))
        return

    managed = [p for p in (agent.managed_platforms or ['facebook', 'instagram']) if p != 'linkedin']

    # ── Fetch comments from each connected, managed platform ─────────────────
    raw_comments = _fetch_comments_from_platforms(agent, managed)

    for comment_data in raw_comments:
        comment_text = comment_data.get('text', '')
        platform = comment_data.get('platform', 'Generic')

        if not comment_text:
            continue

        try:
            result = brain.process_comment(comment_text, platform=platform)

            ModerationLog.objects.create(
                agent=agent,
                platform=platform,
                comment_text=comment_text,
                action_taken=result['action'],
                sentiment_score=result.get('sentiment'),
                confidence_score=result.get('confidence'),
                requires_human=result.get('requires_human', False),
            )

            # ── Execute the action via platform API ───────────────────────────
            if not result.get('requires_human'):
                _execute_moderation_action(agent, comment_data, result)

            logger.info(
                "Moderated comment on %s: action=%s, confidence=%s",
                platform, result['action'], result.get('confidence'),
            )
        except TokenLimitExceeded as exc:
            logger.warning("Token limit hit during moderation for agent %s: %s", agent_id, exc)
            ConversationMessage.objects.create(agent=agent, sender='serea', message_text=str(exc))
            break
        except Exception as exc:
            logger.error("Error moderating comment '%s': %s", comment_text[:40], exc)
            try:
                self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                logger.critical("Max retries exceeded for comment moderation on agent %s.", agent_id)


def _fetch_comments_from_platforms(agent: SereaAgent, managed: list) -> list:
    """
    Fetch recent comments from every active, managed platform account.
    Returns a flat list of comment dicts ready for brain.process_comment().
    Each dict: {text, platform, comment_id, post_id, account_pk, api_platform}
    """
    results = []
    now = timezone.now()

    accounts = SocialMediaAccount.objects.filter(
        agent=agent,
        platform__in=managed,
        is_active=True,
        status='connected',
    )

    for account in accounts:
        try:
            adapter = get_adapter(account.platform, account)
            raw = adapter.fetch_recent_comments(limit=25)
            for c in raw:
                results.append({
                    'text': c.get('text', ''),
                    'platform': account.get_platform_display(),
                    'comment_id': c.get('id', ''),
                    'post_id': c.get('post_id', ''),
                    'account_pk': account.pk,
                    'api_platform': account.platform,
                })
            account.last_checked_at = now
            account.save(update_fields=['last_checked_at'])
        except ValueError:
            logger.info("Skipping unsupported platform %s for agent %s", account.platform, agent.id)
        except PlatformAPIError as exc:
            logger.warning(
                "monitor_social_task: platform API error for %s account %s: %s",
                account.platform, account.pk, exc,
            )
            account.status = 'error'
            account.save(update_fields=['status'])

    return results


def _execute_moderation_action(agent: SereaAgent, comment_data: dict, result: dict) -> None:
    """
    Execute a moderation action (delete / reply) against the platform API.
    Silently logs and continues on failure — the ModerationLog already records the decision.
    """
    action = result.get('action')
    platform = comment_data.get('api_platform', '')
    comment_id = comment_data.get('comment_id', '')
    post_id = comment_data.get('post_id', '')
    response_text = result.get('response_text', '')

    if not comment_id or action in ('flag', 'ignore', 'pending_approval'):
        return

    try:
        account = SocialMediaAccount.objects.get(
            pk=comment_data['account_pk'],
            agent=agent,
        )

        try:
            adapter = get_adapter(platform, account)
        except ValueError:
            logger.warning("No adapter for moderation action on platform %s", platform)
            return

        if action == 'delete':
            adapter.delete_comment(comment_id)
            logger.info("Deleted comment %s on %s", comment_id, platform)
        elif action == 'reply' and response_text:
            adapter.reply_to_comment(comment_id, response_text)
            logger.info("Replied to comment %s on %s", comment_id, platform)

    except PlatformAPIError as exc:
        logger.warning(
            "_execute_moderation_action: API error executing %s on %s comment %s: %s",
            action, platform, comment_id, exc,
        )
    except Exception as exc:
        logger.error(
            "_execute_moderation_action: unexpected error: %s", exc
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. CONTENT SCHEDULER
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def execute_content_task(self, agent_id: int):
    """
    Checks the ContentQueue for items due to be posted and publishes them.
    Schedule: every 5 minutes via Celery Beat.

    Workflow per item:
      1. Fetch metadata from the linked Google Sheet.
      2. Download the visual asset from the linked Google Drive folder.
      3. POST to the linked social network (Meta Graph / Twitter / etc.).
    """
    logger.info("execute_content_task started for agent_id=%s", agent_id)
    now = timezone.now()
    pending_items = ContentQueue.objects.filter(
        agent_id=agent_id,
        status='pending',
        post_date__lte=now,
    ).select_related('agent')

    if not pending_items.exists():
        return

    try:
        brain = SereaBrain(agent_id=agent_id)
    except (TokenLimitExceeded, ValueError) as exc:
        logger.warning("execute_content_task aborted for agent %s: %s", agent_id, exc)
        return

    for item in pending_items:
        try:
            post_id = _publish_content_item(item, brain)
            item.status = 'posted'
            item.platform_post_id = post_id or ''
            item.error_detail = None
            item.save(update_fields=['status', 'platform_post_id', 'error_detail'])
            logger.info(
                "Posted ContentQueue item %s to %s (post_id=%s)",
                item.id, item.platform, post_id,
            )
        except Exception as exc:
            logger.error("Failed to post ContentQueue item %s: %s", item.id, exc)
            item.status = 'failed'
            item.error_detail = str(exc)
            item.save(update_fields=['status', 'error_detail'])
            try:
                self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                logger.critical("Max retries exceeded for ContentQueue item %s.", item.id)


def _publish_content_item(item: ContentQueue, brain) -> str:
    """
    Publish a single ContentQueue item to its target platform.
    Returns the platform post ID on success, or an empty string.

    ContentQueue.platform uses Title-case strings: 'Facebook', 'Instagram', 'LinkedIn'.
    SocialMediaAccount.platform uses lowercase: 'facebook', 'instagram', 'linkedin'.
    """
    agent = item.agent
    platform_lower = item.platform.lower()

    # Optionally enrich caption from Google Sheet
    caption = item.caption or ''
    if item.sheet_link and not caption:
        try:
            enriched, _ = brain._run(
                brain._build_chat_prompt(),
                f"Use the read_google_sheet tool to fetch the caption for the post titled "
                f"'{item.title}' from this sheet: {item.sheet_link}. "
                "Return only the caption text, nothing else."
            )
            caption = enriched.strip() or caption
        except Exception as sheet_exc:
            logger.warning("Sheet read failed for item %s: %s", item.id, sheet_exc)

    # Build full post text
    hashtag_block = f"\n\n{item.hashtags}" if item.hashtags else ''
    post_text = f"{caption}{hashtag_block}".strip()

    image_url = item.media_url or ''

    # Look up the connected account for this platform
    try:
        account = SocialMediaAccount.objects.get(
            agent=agent,
            platform=platform_lower,
            is_active=True,
            status='connected',
        )
    except SocialMediaAccount.DoesNotExist:
        raise PlatformAPIError(
            f"No active {item.platform} account connected for this agent."
        )

    # LinkedIn removed from active posting — redirect operator to manual posting
    if platform_lower == 'linkedin':
        raise PlatformAPIError(
            "LinkedIn posting is not supported. Remove this item or change the platform."
        )

    try:
        adapter = get_adapter(platform_lower, account)
    except ValueError:
        raise PlatformAPIError(
            f"Automated posting not yet supported for platform: {item.platform}"
        )

    result = adapter.post(
        caption=post_text,
        media_url=image_url or None,
        hashtags=[],
    )
    if not result.success:
        raise PlatformAPIError(result.error or f"Post failed on {item.platform}")
    return result.platform_post_id or ''


# ─────────────────────────────────────────────────────────────────────────────
# 3. DAILY BRIEFING
# ─────────────────────────────────────────────────────────────────────────────

@shared_task
def daily_briefing_task(agent_id: int):
    """
    Generates a human-style morning report and posts it to the console_admin chat.
    Schedule: daily at 09:00 UTC via Celery Beat.
    """
    logger.info("daily_briefing_task started for agent_id=%s", agent_id)
    try:
        agent = SereaAgent.objects.get(id=agent_id)
    except SereaAgent.DoesNotExist:
        logger.error("daily_briefing_task: SereaAgent %s not found.", agent_id)
        return

    try:
        brain = SereaBrain(agent_id=agent_id)
    except (TokenLimitExceeded, ValueError) as exc:
        logger.warning("daily_briefing_task skipped for agent %s: %s", agent_id, exc)
        return

    briefing_text = brain.generate_daily_briefing()

    ConversationMessage.objects.create(
        agent=agent,
        sender='serea',
        message_text=briefing_text,
    )
    logger.info("Daily briefing posted for agent_id=%s", agent_id)


# ─────────────────────────────────────────────────────────────────────────────
# 4. DAILY TASK REPORT
# ─────────────────────────────────────────────────────────────────────────────

@shared_task
def generate_daily_report_task(agent_id: int):
    """
    Builds a structured end-of-day report for the client to review.
    Creates DailyReport + DailyReportItem records from today's activity,
    generates a narrative summary using SereaBrain, then notifies the client in chat.
    Schedule: daily at 20:00 UTC via Celery Beat.
    """
    logger.info("generate_daily_report_task started for agent_id=%s", agent_id)
    today = timezone.now().date()

    try:
        agent = SereaAgent.objects.get(id=agent_id)
    except SereaAgent.DoesNotExist:
        logger.error("generate_daily_report_task: SereaAgent %s not found.", agent_id)
        return

    # Don't overwrite an existing report for today
    if DailyReport.objects.filter(agent=agent, report_date=today).exists():
        logger.info("Daily report already exists for agent %s on %s — skipping.", agent_id, today)
        return

    # ── Collect today's activity ──────────────────────────────────────────────
    tasks_today = SereaTask.objects.filter(
        agent=agent, updated_at__date=today
    ).exclude(status='cancelled')

    mod_logs = ModerationLog.objects.filter(agent=agent, created_at__date=today)

    content_posted = ContentQueue.objects.filter(
        agent=agent, status='posted', updated_at__date=today
    )

    # ── Generate narrative summary via LLM ───────────────────────────────────
    try:
        brain = SereaBrain(agent_id=agent_id)
        task_lines = '\n'.join(
            f"- [{t.get_status_display()}] {t.title}: {(t.result or t.progress_notes or 'no notes')[:120]}"
            for t in tasks_today[:20]
        ) or 'No tasks updated today.'
        mod_line = (
            f"{mod_logs.count()} moderation actions "
            f"({mod_logs.filter(action_taken='deleted').count()} deleted, "
            f"{mod_logs.filter(action_taken='replied').count()} replied, "
            f"{mod_logs.filter(requires_human=True).count()} still waiting on your approval)"
        )
        content_line = f"{content_posted.count()} posts published today"

        prompt = (
            "Write a short end-of-day wrap-up (3-5 sentences, casual tone). "
            "Be honest about what's done, what's still in progress, and anything that needs attention.\n\n"
            f"Tasks today:\n{task_lines}\n\n"
            f"Moderation: {mod_line}\n"
            f"Content: {content_line}"
        )
        summary, _ = brain._run(brain._build_chat_prompt(), prompt)
    except Exception as exc:
        logger.warning("generate_daily_report_task: summary LLM failed for agent %s: %s", agent_id, exc)
        summary = f"Here's what happened today ({today}). Check the items below for details."

    # ── Create the DailyReport record ────────────────────────────────────────
    report = DailyReport.objects.create(
        agent=agent,
        report_date=today,
        summary=summary,
        status='pending',
    )

    order = 0

    # Task items
    outcome_map = {
        'done': 'completed',
        'in_progress': 'in_progress',
        'todo': 'in_progress',
        'waiting_approval': 'waiting_approval',
        'waiting_info': 'in_progress',
    }
    for task in tasks_today[:25]:
        DailyReportItem.objects.create(
            report=report,
            item_type='task',
            title=task.title,
            detail=(task.result or task.progress_notes or task.description)[:500],
            outcome=outcome_map.get(task.status, 'in_progress'),
            linked_task=task,
            order=order,
        )
        order += 1

    # Moderation summary item
    if mod_logs.exists():
        DailyReportItem.objects.create(
            report=report,
            item_type='moderation',
            title=f"Moderation — {mod_logs.count()} actions",
            detail=(
                f"Deleted: {mod_logs.filter(action_taken='deleted').count()}  |  "
                f"Replied: {mod_logs.filter(action_taken='replied').count()}  |  "
                f"Flagged for your approval: {mod_logs.filter(requires_human=True).count()}"
            ),
            outcome='completed',
            order=order,
        )
        order += 1

    # Content items
    for item in content_posted[:10]:
        DailyReportItem.objects.create(
            report=report,
            item_type='post',
            title=f"Posted: {item.title}",
            detail=f"Platform: {item.platform}",
            outcome='completed',
            order=order,
        )
        order += 1

    # Notify client in chat
    ConversationMessage.objects.create(
        agent=agent,
        sender='serea',
        message_text=(
            "Hey! End of day — I've put together today's report. "
            "Head to [Daily Reports](/reports/) to check it over. "
            "If anything looks off, flag it there and I'll sort it out."
        ),
    )
    logger.info("Daily report generated for agent %s on %s — %d items.", agent_id, today, order)


# ─────────────────────────────────────────────────────────────────────────────
# 5. HUMAN-IN-THE-LOOP RESUMPTION
# ─────────────────────────────────────────────────────────────────────────────

@shared_task
def resume_after_approval(permission_message_id: int):
    """
    Called after a client clicks "Approve" on a permission request message.
    Retrieves the pending action context and instructs Serea to execute it.
    """
    logger.info("resume_after_approval started for message_id=%s", permission_message_id)
    try:
        perm_msg = ConversationMessage.objects.select_related('agent').get(
            id=permission_message_id,
            is_permission_request=True,
            permission_granted=True,
        )
    except ConversationMessage.DoesNotExist:
        logger.error(
            "resume_after_approval: ConversationMessage %s not found or not approved.",
            permission_message_id
        )
        return

    agent = perm_msg.agent
    context = perm_msg.pending_action_context or {}
    raw_context = context.get('raw_context', 'No context stored.')

    try:
        brain = SereaBrain(agent_id=agent.id)
    except (TokenLimitExceeded, ValueError) as exc:
        logger.warning("resume_after_approval skipped for agent %s: %s", agent.id, exc)
        ConversationMessage.objects.create(agent=agent, sender='serea',
            message_text=f"I could not execute the approved action: {exc}")
        return

    try:
        output_text, _ = brain._run(
            brain._build_moderation_prompt(),
            f"Got the green light! Here's what was approved: {raw_context}\n\nGo ahead and do it now."
        )
        # Post confirmation back to the chat
        ConversationMessage.objects.create(
            agent=agent,
            sender='serea',
            message_text=f"Done! Here's what I did:\n\n{output_text}",
        )
        # Update the linked ModerationLog if one exists
        if hasattr(perm_msg, 'moderation_log'):
            log = perm_msg.moderation_log
            parsed = _parse_agent_response(output_text)
            log.action_taken = parsed['action']
            log.confidence_score = parsed.get('confidence')
            log.requires_human = False
            log.save(update_fields=['action_taken', 'confidence_score', 'requires_human'])

        agent.status = 'idle'
        agent.save(update_fields=['status'])

    except Exception as exc:
        logger.error("resume_after_approval error for agent %s: %s", agent.id, exc)
        ConversationMessage.objects.create(
            agent=agent,
            sender='serea',
            message_text=f"Hey, something went wrong when I tried to execute that — {exc}. Mind checking and letting me know?",
        )


# ─────────────────────────────────────────────────────────────────────────────
# 5. ASYNC DIRECT CHAT
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# 6. DYNAMIC BEAT DISPATCHERS
# These are the tasks wired into CELERY_BEAT_SCHEDULE (settings.py).
# Each one queries active agents at runtime and fans out to per-agent tasks,
# so no agent PKs need to be hardcoded in the schedule.
# ─────────────────────────────────────────────────────────────────────────────

@shared_task
def dispatch_monitor_to_all_agents():
    """Fan-out: trigger monitor_social_task for every active SereaAgent."""
    pks = list(
        SereaAgent.objects.filter(status__in=['idle', 'working']).values_list('id', flat=True)
    )
    for agent_id in pks:
        monitor_social_task.delay(agent_id)
    logger.info("dispatch_monitor_to_all_agents: queued %d agents", len(pks))


@shared_task
def dispatch_content_to_all_agents():
    """Fan-out: trigger execute_content_task for every active SereaAgent."""
    pks = list(
        SereaAgent.objects.filter(status__in=['idle', 'working']).values_list('id', flat=True)
    )
    for agent_id in pks:
        execute_content_task.delay(agent_id)
    logger.info("dispatch_content_to_all_agents: queued %d agents", len(pks))


@shared_task
def dispatch_briefing_to_all_agents():
    """Fan-out: trigger daily_briefing_task for every active SereaAgent."""
    pks = list(
        SereaAgent.objects.filter(status__in=['idle', 'working']).values_list('id', flat=True)
    )
    for agent_id in pks:
        daily_briefing_task.delay(agent_id)
    logger.info("dispatch_briefing_to_all_agents: queued %d agents", len(pks))


@shared_task
def dispatch_reports_to_all_agents():
    """Fan-out: trigger generate_daily_report_task for every active SereaAgent."""
    pks = list(
        SereaAgent.objects.filter(status__in=['idle', 'working']).values_list('id', flat=True)
    )
    for agent_id in pks:
        generate_daily_report_task.delay(agent_id)
    logger.info("dispatch_reports_to_all_agents: queued %d agents", len(pks))


@shared_task
def process_chat_message_task(agent_id: int, user_message: str, sender_email: str):
    """
    Processes a direct chat message from the client asynchronously.
    Called by the serea send_chat_message view. Stores Serea's reply as a
    ConversationMessage so the UI picks it up on the next poll.
    """
    logger.info("process_chat_message_task for agent %s", agent_id)
    try:
        agent = SereaAgent.objects.get(id=agent_id)
    except SereaAgent.DoesNotExist:
        logger.error("process_chat_message_task: SereaAgent %s not found.", agent_id)
        return

    try:
        brain = SereaBrain(agent_id=agent_id)
        reply = brain.chat(user_message)
    except TokenLimitExceeded as exc:
        reply = str(exc)
    except Exception as exc:
        logger.error("process_chat_message_task error for agent %s: %s", agent_id, exc)
        reply = f"I encountered an issue responding. Please try again. ({exc})"

    ConversationMessage.objects.create(agent=agent, sender='serea', message_text=reply)
