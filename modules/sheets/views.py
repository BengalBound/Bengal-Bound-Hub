import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse

from hub.views import _get_business_for_user
from hub.access import require_employee
from .models import HubSheet


@require_employee
def sheet_list(request, slug):
    biz = _get_business_for_user(slug, request.user)
    sheets = HubSheet.objects.filter(business=biz)
    return render(request, 'sheets/list.html', {'biz': biz, 'sheets': sheets, 'current_business': biz})


@require_employee
def sheet_create(request, slug):
    biz = _get_business_for_user(slug, request.user)
    # Default: 20 rows × 8 cols of empty strings
    default_data = [[''] * 8 for _ in range(20)]
    sheet = HubSheet.objects.create(business=biz, created_by=request.user, data=default_data)
    return redirect('sheets:sheet_edit', slug=slug, pk=sheet.pk)


@require_employee
def sheet_edit(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    sheet = get_object_or_404(HubSheet, pk=pk, business=biz)

    if request.method == 'POST':
        title = request.POST.get('title', sheet.title).strip() or 'Untitled Spreadsheet'
        raw_data = request.POST.get('data', '[]')
        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError:
            data = sheet.data
        sheet.title = title
        sheet.data = data
        sheet.last_edited_by = request.user
        sheet.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
        messages.success(request, 'Spreadsheet saved.')
        return redirect('sheets:sheet_edit', slug=slug, pk=pk)

    return render(request, 'sheets/editor.html', {'biz': biz, 'sheet': sheet, 'current_business': biz})


@require_employee
def sheet_delete(request, slug, pk):
    biz = _get_business_for_user(slug, request.user)
    sheet = get_object_or_404(HubSheet, pk=pk, business=biz, created_by=request.user)
    sheet.delete()
    messages.success(request, 'Spreadsheet deleted.')
    return redirect('sheets:sheet_list', slug=slug)
