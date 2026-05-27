from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST

from hub.views import _get_business_for_user
from .models import AssistantConversation, AssistantMessage, AssistantPromptTemplate


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    conversations = AssistantConversation.objects.filter(
        business=biz, user=request.user, is_archived=False
    ).order_by('-updated_at')[:20]
    templates = AssistantPromptTemplate.objects.filter(business=biz, is_active=True)
    stats = {
        'conversations': AssistantConversation.objects.filter(business=biz, user=request.user).count(),
        'templates': templates.count(),
        'messages': AssistantMessage.objects.filter(conversation__business=biz, conversation__user=request.user).count(),
    }
    return render(request, 'ai_assistant/index.html', {
        'biz': biz, 'conversations': conversations, 'templates': templates, 'stats': stats,
    })


@login_required(login_url='/accounts/login/')
def conversation_new(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        title = request.POST.get('title', '').strip() or 'New Conversation'
        template_id = request.POST.get('template')
        conv = AssistantConversation.objects.create(
            business=biz, user=request.user, title=title,
            context_module=request.POST.get('context_module', '').strip(),
        )
        if template_id:
            tpl = AssistantPromptTemplate.objects.filter(pk=template_id, business=biz).first()
            if tpl:
                AssistantMessage.objects.create(
                    conversation=conv, role='system', content=tpl.prompt,
                )
                tpl.use_count += 1
                tpl.save(update_fields=['use_count'])
        return redirect('ai_assistant:conversation', slug=slug, pk=conv.pk)
    templates = AssistantPromptTemplate.objects.filter(business=biz, is_active=True)
    return render(request, 'ai_assistant/conversation_new.html', {'biz': biz, 'templates': templates})


@login_required(login_url='/accounts/login/')
def conversation(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    conv = get_object_or_404(AssistantConversation, pk=pk, business=biz, user=request.user)
    chat_messages = conv.messages.order_by('created_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send':
            user_content = request.POST.get('message', '').strip()
            if user_content:
                AssistantMessage.objects.create(conversation=conv, role='user', content=user_content)
                reply = (
                    "Thank you for your message. The AI Assistant module is ready to be connected to your preferred AI provider. "
                    "Configure your API key in settings to enable intelligent responses."
                )
                AssistantMessage.objects.create(conversation=conv, role='assistant', content=reply)
                conv.save()
                messages.success(request, 'Message sent.')
        elif action == 'archive':
            conv.is_archived = True
            conv.save(update_fields=['is_archived'])
            messages.info(request, 'Conversation archived.')
            return redirect('ai_assistant:index', slug=slug)
        return redirect('ai_assistant:conversation', slug=slug, pk=pk)
    return render(request, 'ai_assistant/conversation.html', {
        'biz': biz, 'conv': conv, 'chat_messages': chat_messages,
    })


@login_required(login_url='/accounts/login/')
def prompt_templates(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            AssistantPromptTemplate.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', ''),
                prompt=request.POST.get('prompt', ''),
                category=request.POST.get('category', '').strip(),
                module=request.POST.get('module', '').strip(),
                created_by=request.user,
            )
            messages.success(request, 'Template created.')
        elif action == 'delete':
            AssistantPromptTemplate.objects.filter(pk=request.POST.get('template_id'), business=biz).delete()
            messages.success(request, 'Template deleted.')
        return redirect('ai_assistant:prompt_templates', slug=slug)
    all_templates = AssistantPromptTemplate.objects.filter(business=biz).select_related('created_by')
    return render(request, 'ai_assistant/prompt_templates.html', {'biz': biz, 'templates': all_templates})
