"""
modules/factory_ops/api_views.py
Lightweight JSON API for factory_ops — no DRF required.
Auth: session-based (same as regular views). Token auth can be layered later.
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import ProductionOrder, RawMaterial, QCInspection, DailyProductionReport
from .views import _biz


def _production_order_to_dict(order):
    return {
        'id': order.id,
        'order_id': order.order_id,
        'style': order.style,
        'buyer': order.buyer,
        'qty': order.qty,
        'line': order.line,
        'current_stage': order.current_stage,
        'priority': order.priority,
        'start_date': order.start_date.isoformat() if order.start_date else None,
        'target_date': order.target_date.isoformat() if order.target_date else None,
        'progress_pct': order.progress_pct,
        'is_overdue': order.is_overdue,
        'notes': order.notes,
    }


def _material_to_dict(m):
    return {
        'id': m.id,
        'name': m.name,
        'category': m.category,
        'unit': m.unit,
        'stock_qty': float(m.stock_qty),
        'reorder_level': float(m.reorder_level),
        'unit_cost': float(m.unit_cost),
        'supplier': m.supplier,
        'is_low_stock': m.stock_qty <= m.reorder_level,
    }


@login_required
@require_GET
def api_production_orders(request, slug):
    """GET /hub/<slug>/factory/api/production/ — list active production orders."""
    try:
        biz = _biz(request, slug)
    except Exception:
        return JsonResponse({'error': 'Not found or no access'}, status=404)

    stage_filter = request.GET.get('stage', '')
    qs = ProductionOrder.objects.filter(business=biz)
    if stage_filter:
        qs = qs.filter(current_stage=stage_filter)
    qs = qs.exclude(current_stage='shipped').order_by('-created_at')[:100]

    return JsonResponse({
        'count': qs.count(),
        'results': [_production_order_to_dict(o) for o in qs],
    })


@login_required
@require_GET
def api_production_order_detail(request, slug, pk):
    """GET /hub/<slug>/factory/api/production/<pk>/"""
    try:
        biz = _biz(request, slug)
    except Exception:
        return JsonResponse({'error': 'Not found'}, status=404)

    try:
        order = ProductionOrder.objects.get(pk=pk, business=biz)
    except ProductionOrder.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    return JsonResponse(_production_order_to_dict(order))


@login_required
@require_GET
def api_raw_materials(request, slug):
    """GET /hub/<slug>/factory/api/materials/ — list all raw materials."""
    try:
        biz = _biz(request, slug)
    except Exception:
        return JsonResponse({'error': 'Not found'}, status=404)

    low_stock_only = request.GET.get('low_stock') == '1'
    qs = RawMaterial.objects.filter(business=biz)
    if low_stock_only:
        from django.db.models import F
        qs = qs.filter(stock_qty__lte=F('reorder_level'))

    return JsonResponse({
        'count': qs.count(),
        'results': [_material_to_dict(m) for m in qs.order_by('name')],
    })


@login_required
@require_GET
def api_qc_summary(request, slug):
    """GET /hub/<slug>/factory/api/qc/ — QC inspection summary."""
    try:
        biz = _biz(request, slug)
    except Exception:
        return JsonResponse({'error': 'Not found'}, status=404)

    from django.utils import timezone
    from django.db.models import Avg
    today = timezone.now().date()

    qs = QCInspection.objects.filter(business=biz, inspection_date=today)
    summary = {
        'date': today.isoformat(),
        'total_inspections': qs.count(),
        'passed': qs.filter(result='pass').count(),
        'failed': qs.filter(result='fail').count(),
        'avg_defect_rate': qs.aggregate(avg=Avg('defect_rate'))['avg'] or 0,
    }
    return JsonResponse(summary)
