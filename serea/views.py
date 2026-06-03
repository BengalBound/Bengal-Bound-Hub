"""
serea/views.py
──────────────
Lightweight JSON API endpoints consumed by the console_admin frontend.

Endpoints:
  POST /serea/permission/<msg_id>/respond/
      Body: { "decision": "approve" | "deny" }
      Called when the client clicks Approve or Deny on a permission request message.
      Queues the resume_after_approval Celery task if approved.

  GET  /serea/agent/<agent_id>/chat/
      Returns the last N ConversationMessages for the given agent as JSON.
      Used for polling-based chat updates (upgrade to Django Channels WebSocket
      for real-time push in a future phase).

  GET  /serea/agent/<agent_id>/logs/
      Returns the recent ModerationLogs for the workspace_admin monitoring panel.
"""

import json
import logging
import threading
import requests as http_requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

from .models import SereaAgent, ConversationMessage, ModerationLog


# ─────────────────────────────────────────────────────────────────────────────
# PERMISSION REQUEST — APPROVE / DENY
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def permission_respond(request, msg_id: int):
    """
    Client approves or denies a pending permission request.

    Expected JSON body:
        { "decision": "approve" }   OR   { "decision": "deny" }
    """
    content_type = request.content_type or ''
    if 'application/json' in content_type:
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
        decision = body.get('decision', '').lower()
    else:
        # Plain HTML form submit (multipart/form-data or application/x-www-form-urlencoded)
        decision = request.POST.get('decision', '').lower()
    if decision not in ('approve', 'deny'):
        return JsonResponse({'error': 'decision must be "approve" or "deny".'}, status=400)

    # Atomic update: only succeeds if the row hasn't been resolved yet.
    # This eliminates the read-check-write race condition.
    updated = ConversationMessage.objects.filter(
        id=msg_id,
        is_permission_request=True,
        agent__tenant=request.user,
        permission_granted__isnull=True,  # guard: not yet resolved
    ).update(permission_granted=(decision == 'approve'))

    if not updated:
        # Either the message doesn't exist / wrong tenant, or was already resolved.
        try:
            ConversationMessage.objects.get(id=msg_id, is_permission_request=True, agent__tenant=request.user)
            return JsonResponse({'error': 'This permission request has already been resolved.'}, status=409)
        except ConversationMessage.DoesNotExist:
            from django.http import Http404
            raise Http404

    perm_msg = ConversationMessage.objects.get(id=msg_id)

    if perm_msg.permission_granted:
        # Wake up the paused Celery task to execute the approved action
        from .tasks import resume_after_approval
        try:
            resume_after_approval.delay(perm_msg.id)
        except Exception:
            # Celery broker unavailable — run in a background thread so the HTTP response
            # returns immediately and the spinner doesn't block waiting for the LLM call.
            t = threading.Thread(target=resume_after_approval, args=(perm_msg.id,), daemon=True)
            t.start()
        status_text = 'approved'
    else:
        # Post a denial acknowledgement to the chat so Serea knows
        ConversationMessage.objects.create(
            agent=perm_msg.agent,
            sender='serea',
            message_text='Understood. I will skip this action as instructed.',
        )
        # Reset agent status back to idle
        agent = perm_msg.agent
        if agent.status == 'waiting':
            agent.status = 'idle'
            agent.save(update_fields=['status'])
        status_text = 'denied'

    # Broadcast updated permission request state via Channels WebSocket
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()
    if channel_layer:
        payload = {
            'id': perm_msg.id,
            'sender': perm_msg.sender,
            'text': perm_msg.message_text,
            'is_permission_request': perm_msg.is_permission_request,
            'permission_granted': perm_msg.permission_granted,
            'created_at': perm_msg.created_at.isoformat(),
        }
        async_to_sync(channel_layer.group_send)(
            f'agent_{perm_msg.agent_id}',
            {
                'type': 'chat_message',
                'message': payload
            }
        )

    is_ajax = 'application/json' in (request.content_type or '')
    if is_ajax:
        return JsonResponse({'status': status_text, 'message_id': msg_id})
    # Form submit — redirect back to the referring page (my_ai or ai_chat)
    return redirect(request.META.get('HTTP_REFERER', '/my-ai/'))


# ─────────────────────────────────────────────────────────────────────────────
# CHAT HISTORY (polling fallback — upgrade to Channels WebSocket later)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_GET
def agent_chat(request, agent_id: int):
    """Returns the last 50 ConversationMessages for the given agent."""
    agent = get_object_or_404(SereaAgent, id=agent_id, tenant=request.user)
    msgs = ConversationMessage.objects.filter(agent=agent).order_by('-created_at')[:50]

    data = [
        {
            'id': m.id,
            'sender': m.sender,
            'text': m.message_text,
            'is_permission_request': m.is_permission_request,
            'permission_granted': m.permission_granted,
            'created_at': m.created_at.isoformat(),
        }
        for m in reversed(list(msgs))
    ]
    return JsonResponse({'agent_id': agent_id, 'messages': data})


# ─────────────────────────────────────────────────────────────────────────────
# MODERATION LOGS (workspace_admin monitoring panel)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_GET
def agent_logs(request, agent_id: int):
    """Returns the last 100 ModerationLogs for a given agent (tenant-scoped)."""
    agent = get_object_or_404(SereaAgent, id=agent_id, tenant=request.user)
    logs = ModerationLog.objects.filter(agent=agent).order_by('-created_at')[:100]

    data = [
        {
            'id': log.id,
            'platform': log.platform,
            'comment': log.comment_text[:120],
            'action': log.action_taken,
            'confidence': log.confidence_score,
            'sentiment': log.sentiment_score,
            'requires_human': log.requires_human,
            'created_at': log.created_at.isoformat(),
        }
        for log in logs
    ]
    return JsonResponse({'agent_id': agent_id, 'logs': data})


# ─────────────────────────────────────────────────────────────────────────────
# SEND CHAT MESSAGE (AJAX — used by console_admin chat with async fallback)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def send_chat_message(request, agent_id: int):
    """
    AJAX endpoint to send a message to a Serea agent and trigger an async reply.

    POST body (JSON): { "message": "your text here" }

    Returns immediately with the stored client message ID and a 'pending' state.
    The actual LLM reply is queued via process_chat_message_task (Celery).
    The frontend can poll agent_chat to pick up the reply once it arrives.

    Falls back to synchronous processing if Celery is not available.
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    message_text = body.get('message', '').strip()
    if not message_text:
        return JsonResponse({'error': 'message is required.'}, status=400)

    agent = get_object_or_404(SereaAgent, id=agent_id, tenant=request.user)

    if agent.status == 'offline':
        return JsonResponse({'error': 'This agent is currently offline.'}, status=403)

    # Store the client's message
    client_msg = ConversationMessage.objects.create(
        agent=agent,
        sender=request.user.email,
        message_text=message_text,
    )

    # Queue Serea's reply asynchronously
    try:
        from .tasks import process_chat_message_task
        process_chat_message_task.delay(agent.id, message_text, request.user.email)
        async_mode = True
    except Exception:
        # Fallback: process synchronously if Celery broker is unavailable
        from .logic import SereaBrain, TokenLimitExceeded
        async_mode = False
        try:
            brain = SereaBrain(agent_id=agent.id)
            reply = brain.chat(message_text)
        except TokenLimitExceeded as exc:
            reply = str(exc)
        except Exception as exc:
            reply = f"I encountered an issue. Please try again. ({exc})"
        ConversationMessage.objects.create(
            agent=agent,
            sender='serea',
            message_text=reply,
        )

    return JsonResponse({
        'status': 'ok',
        'message_id': client_msg.id,
        'async': async_mode,
    })


# ─────────────────────────────────────────────────────────────────────────────
# FACEBOOK WEBHOOK — receive DMs & comments, reply via Graph API
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def facebook_webhook(request):
    """
    GET  — Facebook webhook verification challenge (hub.mode / hub.verify_token / hub.challenge).
    POST — Incoming page events (Messenger DMs, comment replies, postbacks).

    Set FACEBOOK_WEBHOOK_VERIFY_TOKEN in your .env to a secret string, then enter
    the same token in the Facebook Developer Console when configuring the webhook.
    Webhook callback URL: https://<your-domain>/serea/webhook/facebook/
    Subscribe to fields: messages, messaging_postbacks
    """
    if request.method == 'GET':
        mode      = request.GET.get('hub.mode')
        token     = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        expected  = getattr(settings, 'FACEBOOK_WEBHOOK_VERIFY_TOKEN', 'serea_webhook_verify')
        if mode == 'subscribe' and token == expected:
            logger.info("Facebook webhook verified successfully.")
            return HttpResponse(challenge, content_type='text/plain')
        logger.warning("Facebook webhook verification failed — token mismatch.")
        return HttpResponse('Verification failed', status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return HttpResponse('EVENT_RECEIVED', content_type='text/plain')

        logger.info("Facebook webhook POST received: %s", json.dumps(data)[:500])
        print(f"[SEREA WEBHOOK] Received: {json.dumps(data)[:500]}")  # visible in dev server terminal

        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                page_id = str(entry.get('id', ''))
                for event in entry.get('messaging', []):
                    # Skip echo events (messages the page itself sent)
                    if event.get('message', {}).get('is_echo'):
                        continue
                    sender_id    = event.get('sender', {}).get('id', '')
                    message_obj  = event.get('message', {})
                    message_text = message_obj.get('text', '').strip()
                    print(f"[SEREA WEBHOOK] page_id={page_id} sender={sender_id} text={message_text!r}")
                    if not message_text or not sender_id:
                        continue
                    # Don't reply to our own page's sender ID
                    if sender_id == page_id:
                        continue
                    t = threading.Thread(
                        target=_handle_facebook_dm,
                        args=(page_id, sender_id, message_text),
                        daemon=True,
                    )
                    t.start()

        # Facebook requires a fast 200 response — always return this immediately
        return HttpResponse('EVENT_RECEIVED', content_type='text/plain')

    return HttpResponse(status=405)


def _handle_facebook_dm(page_id: str, sender_psid: str, message_text: str):
    """
    Background thread: look up the agent for this FB page, run Serea's brain,
    send the reply back via the Graph API, and log the exchange in console_admin.
    """
    from .models import SocialMediaAccount, ConversationMessage
    from .logic import SereaBrain, TokenLimitExceeded

    account = SocialMediaAccount.objects.select_related('agent').filter(
        platform='facebook',
        account_id=page_id,
        status='connected',
    ).first()
    if not account:
        logger.warning("facebook_webhook: no connected account for page_id=%s", page_id)
        return

    agent = account.agent

    # Store the incoming customer message for conversation history (per PSID thread)
    ConversationMessage.objects.create(
        agent=agent,
        sender=f'facebook_user:{sender_psid}',
        message_text=f"[Facebook DM] {message_text}",
    )

    # Generate a natural customer-facing reply
    try:
        brain = SereaBrain(agent_id=agent.id)
        reply = brain.reply_to_customer_dm(
            sender_psid=sender_psid,
            message_text=message_text,
            page_name=account.account_name,
        )
    except TokenLimitExceeded as exc:
        reply = "Hey! Thanks for reaching out. We'll get back to you very shortly!"
        logger.warning("Token limit hit for facebook DM agent %s: %s", agent.id, exc)
    except Exception as exc:
        logger.error("SereaBrain error handling FB DM for agent %s: %s", agent.id, exc)
        return

    # Send reply via Facebook Send API
    sent = _send_facebook_reply(sender_psid, reply, account.access_token)

    # Store Serea's reply with a PSID-scoped sender so history is per-thread
    status_tag = "" if sent else "[FAILED TO SEND] "
    ConversationMessage.objects.create(
        agent=agent,
        sender=f'serea_fb:{sender_psid}',
        message_text=f"{status_tag}{reply}",
    )
    # Also log in the main console feed so the client can see it
    if not sent:
        ConversationMessage.objects.create(
            agent=agent,
            sender='serea',
            message_text=f"⚠️ Failed to send Facebook reply to customer {sender_psid} — check your page access token.",
        )


def _send_facebook_reply(recipient_psid: str, text: str, page_access_token: str) -> bool:
    """POST a text reply to a Messenger user via the Facebook Send API. Returns True on success."""
    url = "https://graph.facebook.com/v18.0/me/messages"
    try:
        resp = http_requests.post(
            url,
            params={'access_token': page_access_token},
            json={
                'recipient': {'id': recipient_psid},
                'message': {'text': text[:2000]},  # Messenger text limit
                'messaging_type': 'RESPONSE',
            },
            timeout=10,
        )
        if resp.status_code == 200:
            logger.info("Facebook reply sent to PSID %s", recipient_psid)
            return True
        else:
            logger.error(
                "Facebook Send API error %s for PSID %s: %s",
                resp.status_code, recipient_psid, resp.text[:200],
            )
            from .models import SocialMediaAccount
            SocialMediaAccount.objects.filter(
                platform='facebook', account_id=recipient_psid
            ).update(status='error', last_error=resp.text[:300])
            return False
    except Exception as exc:
        logger.error("Failed to send Facebook reply to %s: %s", recipient_psid, exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# INSTAGRAM WEBHOOK — receive DMs & comments via Meta Webhooks
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def instagram_webhook(request):
    """
    GET  — Instagram webhook verification (same hub.verify_token mechanic as Facebook).
    POST — Incoming Instagram events: messages, comments, mentions.

    Set INSTAGRAM_WEBHOOK_VERIFY_TOKEN in your .env (can share with Facebook token).
    Webhook callback URL: https://<your-domain>/serea/webhook/instagram/
    Subscribe to fields: messages, comments, mentions
    """
    if request.method == 'GET':
        mode      = request.GET.get('hub.mode')
        token     = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        expected  = getattr(settings, 'INSTAGRAM_WEBHOOK_VERIFY_TOKEN',
                            getattr(settings, 'FACEBOOK_WEBHOOK_VERIFY_TOKEN', 'serea_webhook_verify'))
        if mode == 'subscribe' and token == expected:
            logger.info("Instagram webhook verified successfully.")
            return HttpResponse(challenge, content_type='text/plain')
        logger.warning("Instagram webhook verification failed — token mismatch.")
        return HttpResponse('Verification failed', status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return HttpResponse('EVENT_RECEIVED', content_type='text/plain')

        logger.info("Instagram webhook POST received: %s", json.dumps(data)[:500])

        if data.get('object') == 'instagram':
            for entry in data.get('entry', []):
                ig_account_id = str(entry.get('id', ''))

                # Handle direct messages
                for event in entry.get('messaging', []):
                    if event.get('message', {}).get('is_echo'):
                        continue
                    sender_id   = event.get('sender', {}).get('id', '')
                    message_obj = event.get('message', {})
                    text        = message_obj.get('text', '').strip()
                    if text and sender_id and sender_id != ig_account_id:
                        t = threading.Thread(
                            target=_handle_instagram_dm,
                            args=(ig_account_id, sender_id, text),
                            daemon=True,
                        )
                        t.start()

                # Handle comment events
                for change in entry.get('changes', []):
                    if change.get('field') == 'comments':
                        comment_data = change.get('value', {})
                        _handle_instagram_comment(ig_account_id, comment_data)

        return HttpResponse('EVENT_RECEIVED', content_type='text/plain')

    return HttpResponse(status=405)


def _handle_instagram_dm(ig_account_id: str, sender_id: str, message_text: str):
    """
    Background thread: look up the agent for this Instagram account, run Serea's brain,
    send the reply back via the Graph API, and log the exchange.
    """
    from .models import SocialMediaAccount, ConversationMessage
    from .logic import SereaBrain, TokenLimitExceeded

    account = SocialMediaAccount.objects.select_related('agent').filter(
        platform='instagram',
        account_id=ig_account_id,
        status='connected',
    ).first()
    if not account:
        logger.warning("instagram_webhook: no connected account for ig_account_id=%s", ig_account_id)
        return

    agent = account.agent

    ConversationMessage.objects.create(
        agent=agent,
        sender=f'instagram_user:{sender_id}',
        message_text=f"[Instagram DM] {message_text}",
    )

    try:
        brain = SereaBrain(agent_id=agent.id)
        reply = brain.reply_to_customer_dm(
            sender_psid=sender_id,
            message_text=message_text,
            page_name=account.account_name,
        )
    except TokenLimitExceeded as exc:
        logger.warning("Token limit hit for Instagram DM agent %s: %s", agent.id, exc)
        return
    except Exception as exc:
        logger.error("SereaBrain error handling Instagram DM for agent %s: %s", agent.id, exc)
        return

    # Send reply via Instagram Messenger API (same Graph API endpoint)
    sent = _send_instagram_reply(sender_id, reply, account.access_token)

    status_tag = "" if sent else "[FAILED TO SEND] "
    ConversationMessage.objects.create(
        agent=agent,
        sender=f'serea_ig:{sender_id}',
        message_text=f"{status_tag}{reply}",
    )
    if not sent:
        ConversationMessage.objects.create(
            agent=agent,
            sender='serea',
            message_text=f"Failed to send Instagram reply to customer {sender_id} — check your Instagram access token.",
        )


def _handle_instagram_comment(ig_account_id: str, comment_data: dict):
    """
    Handles an incoming Instagram comment change event.
    Routes to Serea's comment moderation brain.
    """
    from .models import SocialMediaAccount, ModerationLog
    from .logic import SereaBrain, TokenLimitExceeded

    comment_text = comment_data.get('text', '').strip()
    if not comment_text:
        return

    account = SocialMediaAccount.objects.select_related('agent').filter(
        platform='instagram',
        account_id=ig_account_id,
        status='connected',
    ).first()
    if not account:
        return

    agent = account.agent
    try:
        brain = SereaBrain(agent_id=agent.id)
        result = brain.process_comment(comment_text, platform='Instagram')
        ModerationLog.objects.create(
            agent=agent,
            platform='Instagram',
            comment_text=comment_text,
            action_taken=result['action'],
            sentiment_score=result.get('sentiment'),
            confidence_score=result.get('confidence'),
            requires_human=result.get('requires_human', False),
        )
    except TokenLimitExceeded as exc:
        logger.warning("Token limit hit for Instagram comment agent %s: %s", agent.id, exc)
    except Exception as exc:
        logger.error("Error handling Instagram comment for agent %s: %s", agent.id, exc)


def _send_instagram_reply(recipient_id: str, text: str, access_token: str) -> bool:
    """Send a reply to an Instagram DM via the Graph API. Returns True on success."""
    url = "https://graph.facebook.com/v18.0/me/messages"
    try:
        resp = http_requests.post(
            url,
            params={'access_token': access_token},
            json={
                'recipient': {'id': recipient_id},
                'message': {'text': text[:1000]},  # Instagram message limit
                'messaging_type': 'RESPONSE',
            },
            timeout=10,
        )
        if resp.status_code == 200:
            logger.info("Instagram reply sent to user %s", recipient_id)
            return True
        else:
            logger.error(
                "Instagram Send API error %s for user %s: %s",
                resp.status_code, recipient_id, resp.text[:200],
            )
            return False
    except Exception as exc:
        logger.error("Failed to send Instagram reply to %s: %s", recipient_id, exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# LINKEDIN — comment moderation (poll-based; LinkedIn webhooks require app review)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def trigger_linkedin_moderation(request, agent_id: int):
    """
    Manually triggers Serea to moderate a LinkedIn comment.
    Used when client pastes a comment in the dashboard for Serea to evaluate.

    POST body (JSON):
        { "comment_text": "...", "comment_url": "..." }
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    comment_text = body.get('comment_text', '').strip()
    if not comment_text:
        return JsonResponse({'error': 'comment_text is required.'}, status=400)

    agent = get_object_or_404(SereaAgent, id=agent_id, tenant=request.user)

    try:
        from .logic import SereaBrain
        from .models import ModerationLog
        brain = SereaBrain(agent_id=agent.id)
        result = brain.process_comment(comment_text, platform='LinkedIn')
        log = ModerationLog.objects.create(
            agent=agent,
            platform='LinkedIn',
            comment_text=comment_text,
            action_taken=result['action'],
            sentiment_score=result.get('sentiment'),
            confidence_score=result.get('confidence'),
            requires_human=result.get('requires_human', False),
        )
        return JsonResponse({
            'status': 'ok',
            'log_id': log.id,
            'action': result['action'],
            'confidence': result.get('confidence'),
            'sentiment': result.get('sentiment'),
            'requires_human': result.get('requires_human', False),
            'response': result.get('response_text', '')[:500],
        })
    except Exception as exc:
        logger.error("trigger_linkedin_moderation error for agent %s: %s", agent_id, exc)
        return JsonResponse({'error': str(exc)}, status=500)
