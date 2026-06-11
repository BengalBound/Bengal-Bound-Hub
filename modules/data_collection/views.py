from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hub.models import BusinessInstance, BusinessEmployee
from .models import DataForm, FormField, FormResponse, FieldResponse


def _check(slug, user, min_level=1):
    biz = get_object_or_404(BusinessInstance, slug=slug)
    try:
        emp = BusinessEmployee.objects.get(business=biz, user=user, is_active=True)
    except BusinessEmployee.DoesNotExist:
        return None, None, None
    level = emp.access_level_numeric
    if level < min_level:
        return biz, emp, None
    return biz, emp, level


@login_required
def dc_home(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    forms = DataForm.objects.filter(business=biz)
    total_forms = forms.count()
    active_forms = forms.filter(is_active=True).count()
    total_responses = FormResponse.objects.filter(form__business=biz).count()

    recent_forms = forms.order_by('-created_at')[:6]

    return render(request, 'data_collection/home.html', {
        'biz': biz,
        'access_level': level,
        'stats': {
            'total_forms': total_forms,
            'active_forms': active_forms,
            'total_responses': total_responses,
        },
        'recent_forms': recent_forms,
    })


@login_required
def form_list(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'create_form':
            form = DataForm.objects.create(
                business=biz,
                title=request.POST.get('title', ''),
                description=request.POST.get('description', ''),
                form_type=request.POST.get('form_type', 'survey'),
                is_anonymous='is_anonymous' in request.POST,
                created_by=emp,
            )
            messages.success(request, f'Form "{form.title}" created.')
            return redirect('data_collection:form_builder', slug=slug, form_id=form.pk)
        elif action == 'toggle_form':
            form = get_object_or_404(DataForm, pk=request.POST.get('form_id'), business=biz)
            form.is_active = not form.is_active
            form.save(update_fields=['is_active'])
            messages.success(request, 'Form status updated.')
        return redirect('data_collection:form_list', slug=slug)

    type_filter = request.GET.get('type', '')
    forms = DataForm.objects.filter(business=biz).order_by('-created_at')
    if type_filter:
        forms = forms.filter(form_type=type_filter)

    return render(request, 'data_collection/form_list.html', {
        'biz': biz,
        'access_level': level,
        'forms': forms,
        'type_filter': type_filter,
        'form_types': DataForm.FORM_TYPE_CHOICES,
    })


@login_required
def form_builder(request, slug, form_id):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    form = get_object_or_404(DataForm, pk=form_id, business=biz)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')

        if action == 'add_field':
            last_order = form.fields.order_by('-order').values_list('order', flat=True).first() or 0
            FormField.objects.create(
                form=form,
                field_type=request.POST.get('field_type', 'text'),
                label=request.POST.get('label', ''),
                placeholder=request.POST.get('placeholder', ''),
                options=request.POST.get('options', ''),
                is_required='is_required' in request.POST,
                order=last_order + 1,
            )
            messages.success(request, 'Field added.')

        elif action == 'delete_field':
            field = get_object_or_404(FormField, pk=request.POST.get('field_id'), form=form)
            field.delete()
            messages.success(request, 'Field removed.')

        elif action == 'update_form':
            form.title = request.POST.get('title', form.title)
            form.description = request.POST.get('description', form.description)
            form.form_type = request.POST.get('form_type', form.form_type)
            form.is_anonymous = 'is_anonymous' in request.POST
            form.save()
            messages.success(request, 'Form updated.')

        return redirect('data_collection:form_builder', slug=slug, form_id=form_id)

    fields = form.fields.all()
    return render(request, 'data_collection/form_builder.html', {
        'biz': biz,
        'access_level': level,
        'form': form,
        'fields': fields,
        'field_types': FormField.FIELD_TYPE_CHOICES,
        'form_types': DataForm.FORM_TYPE_CHOICES,
    })


@login_required
def form_detail(request, slug, form_id):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    form = get_object_or_404(DataForm, pk=form_id, business=biz)
    responses = FormResponse.objects.filter(form=form).prefetch_related(
        'field_responses__field'
    ).order_by('-submitted_at')
    fields = list(form.fields.all())

    return render(request, 'data_collection/form_detail.html', {
        'biz': biz,
        'access_level': level,
        'form': form,
        'responses': responses,
        'fields': fields,
    })


def public_form(request, slug, form_id):
    biz = get_object_or_404(BusinessInstance, slug=slug)
    form = get_object_or_404(DataForm, pk=form_id, business=biz, is_active=True)
    fields = form.fields.all()

    if request.method == 'POST':
        resp = FormResponse.objects.create(
            form=form,
            respondent_name=request.POST.get('respondent_name', ''),
            respondent_email=request.POST.get('respondent_email', ''),
        )
        for field in fields:
            value = request.POST.get(f'field_{field.pk}', '')
            if value:
                FieldResponse.objects.create(form_response=resp, field=field, value=value)
        return render(request, 'data_collection/form_thankyou.html', {'biz': biz, 'form': form})

    return render(request, 'data_collection/public_form.html', {
        'biz': biz,
        'form': form,
        'fields': fields,
    })
