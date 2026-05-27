import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt

from hub.views import _get_business_for_user
from hub.access import require_employee
from .models import HubForm, HubFormField, HubFormResponse


@require_employee
def form_list(request, slug):
    biz = _get_business_for_user(slug, request.user)
    forms = HubForm.objects.filter(business=biz)
    return render(request, 'forms_builder/list.html', {'biz': biz, 'forms': forms, 'current_business': biz})


@require_employee
def form_create(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if request.method == 'POST':
        title = request.POST.get('title', 'Untitled Form').strip()
        description = request.POST.get('description', '').strip()
        base_slug = slugify(title)[:80]
        s = base_slug
        i = 1
        while HubForm.objects.filter(slug=s).exists():
            s = f"{base_slug}-{i}"
            i += 1
        form = HubForm.objects.create(business=biz, title=title, description=description, slug=s, created_by=request.user)
        return redirect('forms_builder:form_edit', slug=slug, pk=form.pk)
    return render(request, 'forms_builder/create.html', {'biz': biz, 'current_business': biz})


@require_employee
def form_edit(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    form = get_object_or_404(HubForm, pk=pk, business=biz)
    fields = form.fields.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_form':
            form.title = request.POST.get('title', form.title).strip()
            form.description = request.POST.get('description', '').strip()
            form.accepts_responses = request.POST.get('accepts_responses') == '1'
            form.save()
            messages.success(request, 'Form updated.')
        elif action == 'add_field':
            pos = fields.count()
            HubFormField.objects.create(
                form=form,
                label=request.POST.get('label', 'New Field'),
                field_type=request.POST.get('field_type', 'text'),
                is_required=request.POST.get('is_required') == '1',
                placeholder=request.POST.get('placeholder', ''),
                help_text=request.POST.get('help_text', ''),
                options=json.loads(request.POST.get('options', '[]')),
                position=pos,
            )
            messages.success(request, 'Field added.')
        elif action == 'delete_field':
            HubFormField.objects.filter(pk=request.POST.get('field_id'), form=form).delete()
            messages.info(request, 'Field removed.')
        return redirect('forms_builder:form_edit', slug=slug, pk=pk)

    return render(request, 'forms_builder/editor.html', {
        'biz': biz, 'form': form, 'fields': fields,
        'field_types': HubFormField.TYPES, 'current_business': biz,
    })


@require_employee
def form_responses(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    form = get_object_or_404(HubForm, pk=pk, business=biz)
    responses = form.responses.all()
    return render(request, 'forms_builder/responses.html', {
        'biz': biz, 'form': form, 'responses': responses, 'fields': form.fields.all(), 'current_business': biz,
    })


def form_public(request, form_slug):
    """Public form submission page — no login required."""
    form = get_object_or_404(HubForm, slug=form_slug, is_active=True)
    if request.method == 'POST' and form.accepts_responses:
        answers = {}
        for field in form.fields.all():
            val = request.POST.getlist(f'field_{field.pk}')
            answers[str(field.pk)] = val[0] if len(val) == 1 else val
        HubFormResponse.objects.create(
            form=form,
            respondent_email=request.POST.get('respondent_email', ''),
            respondent_name=request.POST.get('respondent_name', ''),
            answers=answers,
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        return render(request, 'forms_builder/submitted.html', {'form': form})
    return render(request, 'forms_builder/public_form.html', {'form': form, 'fields': form.fields.all()})


@require_employee
def form_delete(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    form = get_object_or_404(HubForm, pk=pk, business=biz, created_by=request.user)
    form.delete()
    messages.success(request, 'Form deleted.')
    return redirect('forms_builder:form_list', slug=slug)
