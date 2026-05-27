from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from hub.views import _get_business_for_user
from hub.access import require_employee
from .models import HubPresentation, HubSlide


@require_employee
def presentation_list(request, slug):
    biz = _get_business_for_user(slug, request.user)
    presentations = HubPresentation.objects.filter(business=biz)
    return render(request, 'slides/list.html', {'biz': biz, 'presentations': presentations, 'current_business': biz})


@require_employee
def presentation_create(request, slug):
    biz = _get_business_for_user(slug, request.user)
    pres = HubPresentation.objects.create(business=biz, created_by=request.user)
    HubSlide.objects.create(presentation=pres, position=0, layout='title', title='Click to add title')
    return redirect('slides:presentation_edit', slug=slug, pk=pres.pk)


@require_employee
def presentation_edit(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    pres = get_object_or_404(HubPresentation, pk=pk, business=biz)
    slides = pres.slides.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_title':
            pres.title = request.POST.get('title', pres.title).strip() or 'Untitled Presentation'
            pres.theme = request.POST.get('theme', pres.theme)
            pres.save()
            messages.success(request, 'Presentation saved.')
        elif action == 'add_slide':
            pos = slides.count()
            HubSlide.objects.create(presentation=pres, position=pos, layout=request.POST.get('layout', 'content'))
            messages.success(request, 'Slide added.')
        elif action == 'save_slide':
            slide_id = request.POST.get('slide_id')
            slide = get_object_or_404(HubSlide, pk=slide_id, presentation=pres)
            slide.title = request.POST.get('title', '')
            slide.body = request.POST.get('body', '')
            slide.notes = request.POST.get('notes', '')
            slide.background_color = request.POST.get('background_color', '')
            slide.layout = request.POST.get('layout', slide.layout)
            slide.save()
        elif action == 'delete_slide':
            slide_id = request.POST.get('slide_id')
            HubSlide.objects.filter(pk=slide_id, presentation=pres).delete()
            messages.info(request, 'Slide deleted.')
        return redirect('slides:presentation_edit', slug=slug, pk=pk)

    active_slide_id = request.GET.get('slide')
    active_slide = slides.filter(pk=active_slide_id).first() if active_slide_id else slides.first()
    return render(request, 'slides/editor.html', {
        'biz': biz, 'pres': pres, 'slides': slides,
        'active_slide': active_slide, 'current_business': biz,
        'themes': ['dark', 'light', 'corporate', 'minimal'],
        'layouts': HubSlide.LAYOUTS,
    })


@require_employee
def presentation_delete(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    pres = get_object_or_404(HubPresentation, pk=pk, business=biz, created_by=request.user)
    pres.delete()
    messages.success(request, 'Presentation deleted.')
    return redirect('slides:presentation_list', slug=slug)
