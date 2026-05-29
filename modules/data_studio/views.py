import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from hub.views import _get_business_for_user
from hub.access import get_access_level
from .models import DataSet, AnalyticsChart, DataStudioReport


def _ds_check(slug, user, min_level=2):
    biz = _get_business_for_user(slug, user)
    if not biz:
        return None, HttpResponseForbidden()
    if get_access_level(biz, user) < min_level:
        return None, HttpResponseForbidden()
    return biz, None


@login_required(login_url='/accounts/login/')
def studio_home(request, slug):
    biz, err = _ds_check(slug, request.user)
    if err:
        return err

    datasets = DataSet.objects.filter(business=biz)[:6]
    charts = AnalyticsChart.objects.filter(business=biz, is_pinned=True)[:6]
    reports = DataStudioReport.objects.filter(business=biz)[:4]

    return render(request, 'data_studio/home.html', {
        'biz': biz,
        'datasets': datasets,
        'charts': charts,
        'reports': reports,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def dataset_list(request, slug):
    biz, err = _ds_check(slug, request.user)
    if err:
        return err

    level = get_access_level(biz, request.user)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action', 'create')
        if action == 'create_csv' and 'csv_file' in request.FILES:
            f = request.FILES['csv_file']
            text = f.read().decode('utf-8', errors='replace')
            reader = csv.reader(io.StringIO(text))
            rows_raw = list(reader)
            if not rows_raw:
                messages.error(request, "Empty CSV file.")
                return redirect('data_studio:datasets', slug=slug)
            columns = rows_raw[0]
            rows = rows_raw[1:]
            DataSet.objects.create(
                business=biz,
                name=request.POST.get('name', f.name).strip(),
                description=request.POST.get('description', '').strip(),
                source='csv',
                columns=columns,
                rows=rows,
                tags=request.POST.get('tags', '').strip(),
                created_by=request.user,
            )
            messages.success(request, "Dataset imported from CSV.")
        elif action == 'create_manual':
            raw_cols = request.POST.get('columns', '')
            columns = [c.strip() for c in raw_cols.split(',') if c.strip()]
            DataSet.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', '').strip(),
                source='manual',
                columns=columns,
                rows=[],
                tags=request.POST.get('tags', '').strip(),
                created_by=request.user,
            )
            messages.success(request, "Dataset created.")
        return redirect('data_studio:datasets', slug=slug)

    datasets = DataSet.objects.filter(business=biz)
    return render(request, 'data_studio/dataset_list.html', {
        'biz': biz,
        'datasets': datasets,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def dataset_detail(request, slug, dataset_id):
    biz, err = _ds_check(slug, request.user)
    if err:
        return err

    dataset = get_object_or_404(DataSet, pk=dataset_id, business=biz)
    level = get_access_level(biz, request.user)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'add_row' and level >= 3:
            row = [request.POST.get(f"col_{i}", '') for i in range(len(dataset.columns))]
            rows = dataset.rows
            rows.append(row)
            dataset.rows = rows
            dataset.save(update_fields=['rows'])
            messages.success(request, "Row added.")

        elif action == 'delete_row' and level >= 3:
            row_idx = int(request.POST.get('row_idx', -1))
            rows = dataset.rows
            if 0 <= row_idx < len(rows):
                rows.pop(row_idx)
                dataset.rows = rows
                dataset.save(update_fields=['rows'])
                messages.success(request, "Row deleted.")

        elif action == 'create_chart' and level >= 3:
            AnalyticsChart.objects.create(
                business=biz,
                dataset=dataset,
                name=request.POST.get('chart_name', '').strip(),
                chart_type=request.POST.get('chart_type', 'table'),
                x_column=request.POST.get('x_column', '').strip(),
                y_column=request.POST.get('y_column', '').strip(),
                group_column=request.POST.get('group_column', '').strip(),
                is_pinned=bool(request.POST.get('is_pinned')),
                created_by=request.user,
            )
            messages.success(request, "Chart created.")

        return redirect('data_studio:dataset_detail', slug=slug, dataset_id=dataset_id)

    charts = dataset.charts.all()
    display_rows = dataset.rows[:200]

    return render(request, 'data_studio/dataset_detail.html', {
        'biz': biz,
        'dataset': dataset,
        'charts': charts,
        'display_rows': display_rows,
        'chart_types': AnalyticsChart.CHART_TYPES,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def chart_gallery(request, slug):
    biz, err = _ds_check(slug, request.user)
    if err:
        return err

    charts = AnalyticsChart.objects.filter(business=biz).select_related('dataset')
    return render(request, 'data_studio/chart_gallery.html', {
        'biz': biz,
        'charts': charts,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })
