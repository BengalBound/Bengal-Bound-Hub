import secrets
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from hub.views import _get_business_for_user
from hub.access import require_employee, require_manager
from .models import MailAccount, MailMessage


@require_employee
def mail_home(request, slug):
    biz = _get_business_for_user(slug, request.user)
    accounts = MailAccount.objects.filter(business=biz, is_active=True)
    my_account = accounts.filter(assigned_to=request.user).first()
    return render(request, 'business_mail/home.html', {
        'biz': biz, 'accounts': accounts, 'my_account': my_account, 'current_business': biz,
    })


@require_employee
def mail_inbox(request, slug, account_id):
    biz = _get_business_for_user(slug, request.user)
    account = get_object_or_404(MailAccount, pk=account_id, business=biz)
    # Only owner or managers can view others' inboxes
    from hub.access import get_access_level
    level = get_access_level(biz, request.user)
    if account.assigned_to and account.assigned_to != request.user and level < 6:
        messages.error(request, 'You do not have access to this mailbox.')
        return redirect('business_mail:mail_home', slug=slug)

    folder = request.GET.get('folder', 'inbox')
    messages_qs = account.messages.filter(folder=folder)
    search = request.GET.get('q', '').strip()
    if search:
        messages_qs = messages_qs.filter(subject__icontains=search) | messages_qs.filter(from_address__icontains=search)

    # Mark messages read
    account.messages.filter(folder='inbox', is_read=False).update(is_read=True)

    return render(request, 'business_mail/inbox.html', {
        'biz': biz, 'account': account, 'messages': messages_qs,
        'folder': folder, 'search': search,
        'unread_count': account.messages.filter(folder='inbox', is_read=False).count(),
        'current_business': biz,
    })


@require_employee
def mail_compose(request, slug):
    biz = _get_business_for_user(slug, request.user)
    accounts = MailAccount.objects.filter(business=biz, is_active=True)
    reply_to = request.GET.get('reply_to')
    reply_msg = None
    if reply_to:
        reply_msg = MailMessage.objects.filter(pk=reply_to).first()

    if request.method == 'POST':
        from_account_id = request.POST.get('from_account')
        account = get_object_or_404(MailAccount, pk=from_account_id, business=biz)
        to_raw = request.POST.get('to', '')
        to_list = [e.strip() for e in to_raw.split(',') if e.strip()]
        subject = request.POST.get('subject', '').strip()
        body_html = request.POST.get('body', '').strip()
        is_draft = request.POST.get('action') == 'draft'

        thread_id = request.POST.get('thread_id') or secrets.token_hex(8)
        msg = MailMessage.objects.create(
            account=account,
            folder='drafts' if is_draft else 'sent',
            from_address=account.address,
            to_addresses=to_list,
            subject=subject,
            body_html=body_html,
            thread_id=thread_id,
        )
        # Deliver to local accounts within this business
        if not is_draft:
            for email in to_list:
                target_acc = MailAccount.objects.filter(address=email, is_active=True).first()
                if target_acc:
                    MailMessage.objects.create(
                        account=target_acc,
                        folder='inbox',
                        from_address=account.address,
                        to_addresses=to_list,
                        subject=subject,
                        body_html=body_html,
                        thread_id=thread_id,
                    )
        label = 'Draft saved.' if is_draft else 'Email sent.'
        messages.success(request, label)
        return redirect('business_mail:mail_home', slug=slug)

    return render(request, 'business_mail/compose.html', {
        'biz': biz, 'accounts': accounts, 'reply_msg': reply_msg, 'current_business': biz,
    })


@require_employee
def mail_view(request, slug, account_id, msg_id):
    biz = _get_business_for_user(slug, request.user)
    account = get_object_or_404(MailAccount, pk=account_id, business=biz)
    msg = get_object_or_404(MailMessage, pk=msg_id, account=account)
    msg.is_read = True
    msg.save(update_fields=['is_read'])
    thread = MailMessage.objects.filter(thread_id=msg.thread_id, account=account).exclude(pk=msg.pk).order_by('received_at')
    return render(request, 'business_mail/view_message.html', {
        'biz': biz, 'account': account, 'msg': msg, 'thread': thread, 'current_business': biz,
    })


@require_manager
def mail_account_manage(request, slug):
    biz = _get_business_for_user(slug, request.user)
    accounts = MailAccount.objects.filter(business=biz)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            address = request.POST.get('address', '').strip()
            display_name = request.POST.get('display_name', '').strip()
            assigned_id = request.POST.get('assigned_to')
            if address:
                from accounts.models import User
                acc = MailAccount.objects.create(
                    business=biz,
                    address=address,
                    display_name=display_name,
                    assigned_to=User.objects.filter(pk=assigned_id).first() if assigned_id else None,
                )
                messages.success(request, f'Mail account {address} created.')
            else:
                messages.error(request, 'Email address is required.')
        elif action == 'delete':
            MailAccount.objects.filter(pk=request.POST.get('account_id'), business=biz).delete()
            messages.success(request, 'Mail account deleted.')
        return redirect('business_mail:mail_account_manage', slug=slug)

    from accounts.models import User
    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    return render(request, 'business_mail/manage_accounts.html', {
        'biz': biz, 'accounts': accounts, 'employees': employees, 'current_business': biz,
    })
