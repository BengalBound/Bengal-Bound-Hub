import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Q

from hub.views import _get_business_for_user
from .models import (
    TwilioConfig, CallQueue, IVRMenu, IVROption,
    CallLog, AgentCallStatus
)

logger = logging.getLogger(__name__)


def _biz(slug, user):
    return _get_business_for_user(slug, user)


def _get_or_create_agent_status(business, user):
    status, _ = AgentCallStatus.objects.get_or_create(
        business=business, agent=user,
        defaults={'status': 'offline'}
    )
    return status


# ─── Dashboard / Supervisor Wallboard ────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def dashboard(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    queues = CallQueue.objects.filter(business=biz, is_active=True).prefetch_related('agents')
    agent_statuses = AgentCallStatus.objects.filter(business=biz).select_related('agent', 'current_call')

    today = timezone.now().date()
    today_calls = CallLog.objects.filter(business=biz, started_at__date=today)

    stats = {
        'total_today': today_calls.count(),
        'completed_today': today_calls.filter(status='completed').count(),
        'abandoned_today': today_calls.filter(status='abandoned').count(),
        'voicemail_today': today_calls.filter(status='voicemail').count(),
        'avg_duration': today_calls.filter(status='completed').aggregate(a=Avg('duration_seconds'))['a'] or 0,
        'avg_wait': today_calls.filter(status='completed').aggregate(a=Avg('wait_seconds'))['a'] or 0,
        'calls_waiting': today_calls.filter(status='queued').count(),
        'agents_available': agent_statuses.filter(status='available').count(),
        'agents_on_call': agent_statuses.filter(status='on_call').count(),
    }

    twilio_config = TwilioConfig.objects.filter(business=biz).first()
    recent_calls = CallLog.objects.filter(business=biz).select_related('agent', 'queue', 'contact')[:15]

    return render(request, 'call_center/dashboard.html', {
        'biz': biz,
        'queues': queues,
        'agent_statuses': agent_statuses,
        'stats': stats,
        'twilio_config': twilio_config,
        'recent_calls': recent_calls,
    })


# ─── Call Log ─────────────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def call_log(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    qs = CallLog.objects.filter(business=biz).select_related('agent', 'queue', 'contact')

    direction = request.GET.get('direction', '')
    status = request.GET.get('status', '')
    q = request.GET.get('q', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if direction:
        qs = qs.filter(direction=direction)
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(caller_number__icontains=q) | Q(called_number__icontains=q) | Q(notes__icontains=q))
    if date_from:
        qs = qs.filter(started_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(started_at__date__lte=date_to)

    return render(request, 'call_center/call_log.html', {
        'biz': biz,
        'calls': qs[:200],
        'direction': direction,
        'status': status,
        'q': q,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': CallLog.STATUS_CHOICES,
    })


@login_required(login_url='/accounts/login/')
def call_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    call = get_object_or_404(CallLog, pk=pk, business=biz)

    if request.method == 'POST':
        call.notes = request.POST.get('notes', call.notes)
        call.save(update_fields=['notes'])
        messages.success(request, 'Notes saved.')
        return redirect('call_center:call_detail', slug=slug, pk=pk)

    return render(request, 'call_center/call_detail.html', {'biz': biz, 'call': call})


# ─── Agent Console ────────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def agent_console(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    my_status = _get_or_create_agent_status(biz, request.user)
    twilio_config = TwilioConfig.objects.filter(business=biz).first()
    my_queues = CallQueue.objects.filter(business=biz, agents=request.user, is_active=True)
    recent_calls = CallLog.objects.filter(business=biz, agent=request.user).select_related('contact', 'queue')[:20]

    return render(request, 'call_center/agent_console.html', {
        'biz': biz,
        'my_status': my_status,
        'twilio_config': twilio_config,
        'my_queues': my_queues,
        'recent_calls': recent_calls,
        'status_choices': AgentCallStatus.STATUS_CHOICES,
    })


# ─── IVR Builder ──────────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def ivr_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    menus = IVRMenu.objects.filter(business=biz).prefetch_related('options')
    return render(request, 'call_center/ivr_list.html', {'biz': biz, 'menus': menus})


@login_required(login_url='/accounts/login/')
def ivr_detail(request, slug, pk=None):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    menu = get_object_or_404(IVRMenu, pk=pk, business=biz) if pk else None

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'save_menu':
            if menu:
                menu.name = request.POST.get('name', menu.name)
                menu.welcome_message = request.POST.get('welcome_message', menu.welcome_message)
                menu.invalid_message = request.POST.get('invalid_message', menu.invalid_message)
                menu.timeout_seconds = int(request.POST.get('timeout_seconds', menu.timeout_seconds))
                menu.max_retries = int(request.POST.get('max_retries', menu.max_retries))
                menu.save()
            else:
                menu = IVRMenu.objects.create(
                    business=biz,
                    name=request.POST.get('name', 'Main Menu'),
                    welcome_message=request.POST.get('welcome_message', ''),
                    invalid_message=request.POST.get('invalid_message', 'Invalid option, please try again.'),
                    timeout_seconds=int(request.POST.get('timeout_seconds', 10)),
                    max_retries=int(request.POST.get('max_retries', 3)),
                )
            messages.success(request, 'IVR menu saved.')
            return redirect('call_center:ivr_detail', slug=slug, pk=menu.pk)

        if action == 'add_option' and menu:
            digit = request.POST.get('digit')
            if digit and not IVROption.objects.filter(menu=menu, digit=digit).exists():
                queue_id = request.POST.get('queue') or None
                IVROption.objects.create(
                    menu=menu,
                    digit=digit,
                    label=request.POST.get('label', '').strip(),
                    action=request.POST.get('action_type', 'queue'),
                    queue_id=queue_id,
                    transfer_number=request.POST.get('transfer_number', '').strip(),
                    message_text=request.POST.get('message_text', '').strip(),
                )
                messages.success(request, f'Option {digit} added.')
            else:
                messages.error(request, f'Digit {digit} already used or invalid.')
            return redirect('call_center:ivr_detail', slug=slug, pk=menu.pk)

        if action == 'delete_option' and menu:
            opt_id = request.POST.get('option_id')
            IVROption.objects.filter(pk=opt_id, menu=menu).delete()
            messages.success(request, 'Option removed.')
            return redirect('call_center:ivr_detail', slug=slug, pk=menu.pk)

        if action == 'delete_menu' and menu:
            menu.delete()
            messages.success(request, 'IVR menu deleted.')
            return redirect('call_center:ivr_list', slug=slug)

    queues = CallQueue.objects.filter(business=biz, is_active=True)
    options = menu.options.select_related('queue') if menu else []
    available_digits = [str(i) for i in range(10)] + ['*', '#']
    used_digits = list(menu.options.values_list('digit', flat=True)) if menu else []
    free_digits = [d for d in available_digits if d not in used_digits]

    return render(request, 'call_center/ivr_detail.html', {
        'biz': biz,
        'menu': menu,
        'options': options,
        'queues': queues,
        'free_digits': free_digits,
        'action_choices': IVROption.ACTION_CHOICES,
    })


# ─── Queue Management ─────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def queue_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    queues = CallQueue.objects.filter(business=biz).prefetch_related('agents')
    from hub.models import BusinessEmployee
    team = [be.user for be in BusinessEmployee.objects.filter(business=biz).select_related('user')]
    return render(request, 'call_center/queue_list.html', {'biz': biz, 'queues': queues, 'team': team})


@login_required(login_url='/accounts/login/')
def queue_detail(request, slug, pk=None):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    queue = get_object_or_404(CallQueue, pk=pk, business=biz) if pk else None
    from hub.models import BusinessEmployee
    team = [be.user for be in BusinessEmployee.objects.filter(business=biz).select_related('user')]
    ivr_menus = IVRMenu.objects.filter(business=biz, is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        if action == 'delete' and queue:
            queue.delete()
            messages.success(request, 'Queue deleted.')
            return redirect('call_center:queue_list', slug=slug)

        agent_ids = request.POST.getlist('agents')
        ivr_id = request.POST.get('ivr_menu') or None

        data = {
            'name': request.POST.get('name', '').strip() or 'Queue',
            'phone_number': request.POST.get('phone_number', '').strip(),
            'strategy': request.POST.get('strategy', 'round_robin'),
            'max_wait_seconds': int(request.POST.get('max_wait_seconds', 120)),
            'greeting_text': request.POST.get('greeting_text', '').strip(),
            'voicemail_enabled': request.POST.get('voicemail_enabled') == 'on',
            'voicemail_text': request.POST.get('voicemail_text', '').strip(),
            'ivr_menu_id': ivr_id,
        }
        if queue:
            for k, v in data.items():
                setattr(queue, k, v)
            queue.save()
        else:
            queue = CallQueue.objects.create(business=biz, **data)

        queue.agents.set(agent_ids)
        messages.success(request, 'Queue saved.')
        return redirect('call_center:queue_list', slug=slug)

    return render(request, 'call_center/queue_detail.html', {
        'biz': biz, 'queue': queue, 'team': team, 'ivr_menus': ivr_menus,
        'strategy_choices': CallQueue.STRATEGY_CHOICES,
    })


# ─── Settings (Twilio credentials) ───────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def cc_settings(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    config, _ = TwilioConfig.objects.get_or_create(business=biz)

    if request.method == 'POST':
        config.account_sid = request.POST.get('account_sid', '').strip()
        config.auth_token = request.POST.get('auth_token', '').strip()
        config.default_from_number = request.POST.get('default_from_number', '').strip()
        config.twiml_app_sid = request.POST.get('twiml_app_sid', '').strip()
        config.is_active = config.is_configured
        config.save()
        messages.success(request, 'Twilio settings saved.' if config.is_active else 'Settings saved — fill all fields to activate.')
        return redirect('call_center:settings', slug=slug)

    base = f"/hub/{slug}/call-center"
    webhook_urls = {
        'Inbound Voice URL': f"{base}/twilio/inbound/",
        'Status Callback URL': f"{base}/twilio/status/",
        'Token URL (Browser Calls)': f"{base}/twilio/token/",
    }
    return render(request, 'call_center/settings.html', {'biz': biz, 'config': config, 'webhook_urls': webhook_urls})


# ─── API endpoints (JSON) ─────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
@require_GET
def api_queue_stats(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return JsonResponse({'error': 'forbidden'}, status=403)

    today = timezone.now().date()
    today_calls = CallLog.objects.filter(business=biz, started_at__date=today)
    agent_statuses = AgentCallStatus.objects.filter(business=biz).select_related('agent')

    data = {
        'calls_waiting': today_calls.filter(status='queued').count(),
        'total_today': today_calls.count(),
        'completed_today': today_calls.filter(status='completed').count(),
        'abandoned_today': today_calls.filter(status='abandoned').count(),
        'agents': [
            {
                'name': s.agent.get_full_name() or s.agent.email,
                'status': s.status,
                'status_display': s.get_status_display(),
                'since': s.last_status_change.isoformat(),
            }
            for s in agent_statuses
        ],
    }
    return JsonResponse(data)


@login_required(login_url='/accounts/login/')
@require_POST
def api_set_agent_status(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return JsonResponse({'error': 'forbidden'}, status=403)

    try:
        body = json.loads(request.body)
        new_status = body.get('status', 'offline')
    except (json.JSONDecodeError, AttributeError):
        new_status = request.POST.get('status', 'offline')

    valid = [s[0] for s in AgentCallStatus.STATUS_CHOICES]
    if new_status not in valid:
        return JsonResponse({'error': 'invalid status'}, status=400)

    my_status = _get_or_create_agent_status(biz, request.user)
    my_status.status = new_status
    my_status.save(update_fields=['status', 'last_status_change'])
    return JsonResponse({'ok': True, 'status': new_status})


# ─── Twilio Webhooks (no CSRF — validated by Twilio signature header) ─────────

@csrf_exempt
def twilio_inbound(request, slug):
    """
    Twilio calls this URL when a call comes in on an assigned number.
    Returns TwiML that plays the IVR greeting or routes directly to a queue.
    """
    from django.http import HttpResponse as HR
    try:
        biz_qs = __import__('hub.models', fromlist=['BusinessInstance']).BusinessInstance
        biz = biz_qs.objects.filter(slug=slug, is_active=True).first()
    except Exception:
        biz = None

    if not biz:
        return HR('<Response><Say>Sorry, this number is not configured.</Say><Hangup/></Response>',
                  content_type='text/xml')

    called_number = request.POST.get('To', '')
    caller_number = request.POST.get('From', '')
    call_sid = request.POST.get('CallSid', '')

    queue = CallQueue.objects.filter(business=biz, phone_number=called_number, is_active=True).first()

    # Log the call
    call_log = CallLog.objects.create(
        business=biz,
        queue=queue,
        twilio_call_sid=call_sid,
        caller_number=caller_number,
        called_number=called_number,
        direction='inbound',
        status='queued',
    )

    # Auto-match CRM contact by phone number
    try:
        from modules.crm.models import Contact
        contact = Contact.objects.filter(
            business=biz,
            phone=caller_number
        ).first() or Contact.objects.filter(
            business=biz,
            mobile=caller_number
        ).first()
        if contact:
            call_log.contact = contact
            call_log.save(update_fields=['contact'])
    except Exception:
        pass

    # Build TwiML response
    if queue and queue.ivr_menu:
        ivr = queue.ivr_menu
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather numDigits="1" action="/hub/{slug}/call-center/twilio/ivr/{ivr.pk}/" method="POST" timeout="{ivr.timeout_seconds}">
    <Say>{ivr.welcome_message}</Say>
  </Gather>
  <Say>{ivr.invalid_message}</Say>
  <Hangup/>
</Response>"""
    elif queue:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>{queue.greeting_text}</Say>
  <Enqueue waitUrl="" action="/hub/{slug}/call-center/twilio/status/">{queue.name}</Enqueue>
</Response>"""
    else:
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Thank you for calling. All our agents are busy. Please try again later.</Say>
  <Hangup/>
</Response>"""

    return HR(twiml, content_type='text/xml')


@csrf_exempt
def twilio_ivr_response(request, slug, menu_pk):
    """Handle the digit pressed in an IVR menu."""
    from django.http import HttpResponse as HR
    digit = request.POST.get('Digits', '')
    call_sid = request.POST.get('CallSid', '')

    try:
        biz_qs = __import__('hub.models', fromlist=['BusinessInstance']).BusinessInstance
        biz = biz_qs.objects.filter(slug=slug, is_active=True).first()
        menu = IVRMenu.objects.get(pk=menu_pk, business=biz)
    except Exception:
        return HR('<Response><Hangup/></Response>', content_type='text/xml')

    # Log IVR path
    CallLog.objects.filter(twilio_call_sid=call_sid).update(
        ivr_path=digit
    )

    try:
        option = menu.options.get(digit=digit)
    except IVROption.DoesNotExist:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather numDigits="1" action="/hub/{slug}/call-center/twilio/ivr/{menu_pk}/" method="POST" timeout="{menu.timeout_seconds}">
    <Say>{menu.invalid_message}</Say>
  </Gather>
  <Hangup/>
</Response>"""
        return HR(twiml, content_type='text/xml')

    if option.action == 'queue' and option.queue:
        q = option.queue
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>{q.greeting_text}</Say>
  <Enqueue action="/hub/{slug}/call-center/twilio/status/">{q.name}</Enqueue>
</Response>"""
    elif option.action == 'transfer' and option.transfer_number:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Transferring your call now.</Say>
  <Dial>{option.transfer_number}</Dial>
</Response>"""
    elif option.action == 'message':
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>{option.message_text}</Say>
  <Hangup/>
</Response>"""
    elif option.action == 'voicemail':
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Please leave your message after the tone. Press any key when done.</Say>
  <Record action="/hub/{slug}/call-center/twilio/status/" maxLength="120" playBeep="true" finishOnKey="any"/>
</Response>"""
    elif option.action == 'submenu' and option.submenu:
        sub = option.submenu
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather numDigits="1" action="/hub/{slug}/call-center/twilio/ivr/{sub.pk}/" method="POST" timeout="{sub.timeout_seconds}">
    <Say>{sub.welcome_message}</Say>
  </Gather>
  <Hangup/>
</Response>"""
    else:
        twiml = '<Response><Hangup/></Response>'

    return HR(twiml, content_type='text/xml')


@csrf_exempt
def twilio_status(request, slug):
    """Twilio status callback — updates call log when call ends."""
    call_sid = request.POST.get('CallSid', '')
    call_status = request.POST.get('CallStatus', '')
    duration = request.POST.get('CallDuration', 0)
    recording_url = request.POST.get('RecordingUrl', '')
    recording_sid = request.POST.get('RecordingSid', '')

    STATUS_MAP = {
        'completed': 'completed',
        'no-answer': 'no-answer',
        'busy': 'busy',
        'failed': 'failed',
        'canceled': 'abandoned',
    }

    if call_sid:
        update = {
            'status': STATUS_MAP.get(call_status, call_status),
            'duration_seconds': int(duration or 0),
            'ended_at': timezone.now(),
        }
        if recording_url:
            update['recording_url'] = recording_url
        if recording_sid:
            update['recording_sid'] = recording_sid

        CallLog.objects.filter(twilio_call_sid=call_sid).update(**update)

        # Free up the agent
        AgentCallStatus.objects.filter(
            current_call__twilio_call_sid=call_sid
        ).update(status='wrap_up', current_call=None)

    return HttpResponse('', status=204)


@csrf_exempt
def twilio_token(request, slug):
    """
    Generate a Twilio Access Token for Twilio.js browser calls.
    POST — returns JSON {token, identity}.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'unauthenticated'}, status=401)

    try:
        biz_qs = __import__('hub.models', fromlist=['BusinessInstance']).BusinessInstance
        biz = biz_qs.objects.filter(slug=slug, is_active=True).first()
        config = TwilioConfig.objects.get(business=biz, is_active=True)
    except Exception:
        return JsonResponse({'error': 'Twilio not configured'}, status=400)

    try:
        from twilio.jwt.access_token import AccessToken
        from twilio.jwt.access_token.grants import VoiceGrant

        identity = str(request.user.pk)
        token = AccessToken(
            config.account_sid,
            config.auth_token,      # in prod use API Key / Secret instead
            config.auth_token,
            identity=identity,
            ttl=3600,
        )
        grant = VoiceGrant(outgoing_application_sid=config.twiml_app_sid, incoming_allow=True)
        token.add_grant(grant)
        return JsonResponse({'token': token.to_jwt(), 'identity': identity})
    except ImportError:
        return JsonResponse({'error': 'twilio package not installed'}, status=500)
    except Exception as exc:
        logger.error("twilio_token error: %s", exc)
        return JsonResponse({'error': str(exc)}, status=500)
