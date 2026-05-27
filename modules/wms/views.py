from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone

from hub.views import _get_business_for_user
from hub.access import get_access_level
from .models import WarehouseZone, StorageBin, InboundReceipt, InboundReceiptLine, PickList, PickListItem


def _wms_check(slug, user, min_level=2):
    biz = _get_business_for_user(slug, user)
    if not biz:
        return None, HttpResponseForbidden()
    if get_access_level(biz, user) < min_level:
        return None, HttpResponseForbidden()
    return biz, None


def _next_receipt_number(business):
    last = InboundReceipt.objects.filter(business=business).order_by('-pk').first()
    num = int(last.receipt_number) + 1 if last else 1
    return str(num).zfill(5)


def _next_pick_number(business):
    last = PickList.objects.filter(business=business).order_by('-pk').first()
    num = int(last.pick_number) + 1 if last else 1
    return str(num).zfill(5)


@login_required(login_url='/accounts/login/')
def wms_dashboard(request, slug):
    biz, err = _wms_check(slug, request.user)
    if err:
        return err

    zones = WarehouseZone.objects.filter(business=biz, is_active=True)
    total_bins = StorageBin.objects.filter(zone__business=biz).count()
    occupied_bins = StorageBin.objects.filter(zone__business=biz, is_occupied=True).count()

    pending_receipts = InboundReceipt.objects.filter(business=biz, status__in=['expected', 'partial']).count()
    active_picks = PickList.objects.filter(business=biz, status__in=['pending', 'picking']).count()
    recent_picks = PickList.objects.filter(business=biz).select_related('assigned_to')[:8]

    return render(request, 'wms/dashboard.html', {
        'biz': biz,
        'zones': zones,
        'total_bins': total_bins,
        'occupied_bins': occupied_bins,
        'free_bins': total_bins - occupied_bins,
        'occupancy_pct': int(occupied_bins / total_bins * 100) if total_bins else 0,
        'pending_receipts': pending_receipts,
        'active_picks': active_picks,
        'recent_picks': recent_picks,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def zone_list(request, slug):
    biz, err = _wms_check(slug, request.user, min_level=4)
    if err:
        return err

    level = get_access_level(biz, request.user)

    if request.method == 'POST':
        action = request.POST.get('action', 'create_zone')

        if action == 'create_zone':
            zone = WarehouseZone.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                zone_type=request.POST.get('zone_type', 'storage'),
                description=request.POST.get('description', '').strip(),
                capacity_bins=request.POST.get('capacity_bins', '') or None,
            )
            messages.success(request, f"Zone '{zone.name}' created.")

        elif action == 'add_bins':
            zone_id = request.POST.get('zone_id', '')
            prefix = request.POST.get('prefix', '').strip()
            count = int(request.POST.get('count', 1))
            start = int(request.POST.get('start', 1))
            zone = get_object_or_404(WarehouseZone, pk=int(zone_id), business=biz)
            for i in range(start, start + count):
                code = f"{prefix}{str(i).zfill(3)}"
                StorageBin.objects.get_or_create(zone=zone, bin_code=code)
            messages.success(request, f"{count} bins added to {zone.name}.")

        return redirect('wms:zones', slug=slug)

    zones = WarehouseZone.objects.filter(business=biz).prefetch_related('bins')
    return render(request, 'wms/zone_list.html', {
        'biz': biz,
        'zones': zones,
        'zone_types': WarehouseZone.ZONE_TYPES,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def inbound_list(request, slug):
    biz, err = _wms_check(slug, request.user)
    if err:
        return err

    level = get_access_level(biz, request.user)

    if request.method == 'POST' and level >= 3:
        from hub.models import BusinessEmployee
        emp_id = request.POST.get('received_by_id', '')
        receipt = InboundReceipt.objects.create(
            business=biz,
            receipt_number=_next_receipt_number(biz),
            supplier_name=request.POST.get('supplier_name', '').strip(),
            purchase_order_ref=request.POST.get('purchase_order_ref', '').strip(),
            carrier_name=request.POST.get('carrier_name', '').strip(),
            tracking_ref=request.POST.get('tracking_ref', '').strip(),
            expected_date=request.POST.get('expected_date', '') or None,
            received_by_id=int(emp_id) if emp_id else None,
            notes=request.POST.get('notes', '').strip(),
            created_by=request.user,
        )
        messages.success(request, f"GRN-{receipt.receipt_number} created.")
        return redirect('wms:inbound_detail', slug=slug, receipt_id=receipt.pk)

    receipts = InboundReceipt.objects.filter(business=biz).select_related('received_by')
    status_filter = request.GET.get('status', '')
    if status_filter:
        receipts = receipts.filter(status=status_filter)

    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'wms/inbound_list.html', {
        'biz': biz,
        'receipts': receipts,
        'statuses': InboundReceipt.STATUS,
        'status_filter': status_filter,
        'employees': employees,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def inbound_detail(request, slug, receipt_id):
    biz, err = _wms_check(slug, request.user)
    if err:
        return err

    receipt = get_object_or_404(InboundReceipt, pk=receipt_id, business=biz)
    level = get_access_level(biz, request.user)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'add_line' and level >= 3:
            bin_id = request.POST.get('bin_id', '')
            InboundReceiptLine.objects.create(
                receipt=receipt,
                item_description=request.POST.get('item_description', '').strip(),
                sku=request.POST.get('sku', '').strip(),
                expected_qty=request.POST.get('expected_qty', 1),
                unit=request.POST.get('unit', '').strip(),
                bin_id=int(bin_id) if bin_id else None,
            )
            messages.success(request, "Line added.")

        elif action == 'receive' and level >= 3:
            lines = receipt.lines.all()
            for line in lines:
                qty_key = f"received_qty_{line.pk}"
                bin_key = f"bin_{line.pk}"
                new_qty = request.POST.get(qty_key, '')
                bin_id = request.POST.get(bin_key, '')
                if new_qty:
                    line.received_qty = new_qty
                if bin_id:
                    line.bin_id = int(bin_id)
                    line.bin.is_occupied = True
                    line.bin.current_sku = line.sku or line.item_description
                    line.bin.current_qty = line.received_qty
                    line.bin.save(update_fields=['is_occupied', 'current_sku', 'current_qty'])
                line.save(update_fields=['received_qty', 'bin'])

            # Update receipt status
            total_exp = sum(l.expected_qty for l in receipt.lines.all())
            total_rec = sum(l.received_qty for l in receipt.lines.all())
            if total_rec == 0:
                receipt.status = 'expected'
            elif total_rec < total_exp:
                receipt.status = 'partial'
            elif total_rec == total_exp:
                receipt.status = 'complete'
                receipt.received_date = timezone.now().date()
            else:
                receipt.status = 'over'
            receipt.save(update_fields=['status', 'received_date'])
            messages.success(request, "Receipt updated.")

        return redirect('wms:inbound_detail', slug=slug, receipt_id=receipt_id)

    lines = receipt.lines.all()
    bins = StorageBin.objects.filter(zone__business=biz).select_related('zone')
    return render(request, 'wms/inbound_detail.html', {
        'biz': biz,
        'receipt': receipt,
        'lines': lines,
        'bins': bins,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def picklist_list(request, slug):
    biz, err = _wms_check(slug, request.user)
    if err:
        return err

    level = get_access_level(biz, request.user)

    if request.method == 'POST' and level >= 3:
        from hub.models import BusinessEmployee
        emp_id = request.POST.get('assigned_to_id', '')
        pl = PickList.objects.create(
            business=biz,
            pick_number=_next_pick_number(biz),
            order_reference=request.POST.get('order_reference', '').strip(),
            customer_name=request.POST.get('customer_name', '').strip(),
            customer_address=request.POST.get('customer_address', '').strip(),
            assigned_to_id=int(emp_id) if emp_id else None,
            due_date=request.POST.get('due_date', '') or None,
            notes=request.POST.get('notes', '').strip(),
            created_by=request.user,
        )
        messages.success(request, f"Pick list PL-{pl.pick_number} created.")
        return redirect('wms:picklist_detail', slug=slug, pick_id=pl.pk)

    picks = PickList.objects.filter(business=biz).select_related('assigned_to')
    status_filter = request.GET.get('status', '')
    if status_filter:
        picks = picks.filter(status=status_filter)

    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'wms/picklist_list.html', {
        'biz': biz,
        'picks': picks,
        'statuses': PickList.STATUS,
        'status_filter': status_filter,
        'employees': employees,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def picklist_detail(request, slug, pick_id):
    biz, err = _wms_check(slug, request.user)
    if err:
        return err

    pick = get_object_or_404(PickList, pk=pick_id, business=biz)
    level = get_access_level(biz, request.user)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'add_item' and level >= 3:
            bin_id = request.POST.get('bin_id', '')
            PickListItem.objects.create(
                pick_list=pick,
                item_description=request.POST.get('item_description', '').strip(),
                sku=request.POST.get('sku', '').strip(),
                quantity=request.POST.get('quantity', 1),
                unit=request.POST.get('unit', '').strip(),
                bin_id=int(bin_id) if bin_id else None,
            )
            messages.success(request, "Item added.")

        elif action == 'mark_picked' and level >= 2:
            items = pick.items.all()
            for item in items:
                picked_key = f"picked_{item.pk}"
                picked_qty = request.POST.get(picked_key, '')
                if picked_qty:
                    item.picked_qty = picked_qty
                    item.is_picked = float(picked_qty) >= float(item.quantity)
                    item.save(update_fields=['picked_qty', 'is_picked'])
            if pick.items.filter(is_picked=False).count() == 0:
                pick.status = 'picked'
            else:
                pick.status = 'picking'
            pick.save(update_fields=['status'])
            messages.success(request, "Pick progress saved.")

        elif action == 'dispatch' and level >= 3:
            pick.status = 'dispatched'
            pick.courier_name = request.POST.get('courier_name', '').strip()
            pick.tracking_number = request.POST.get('tracking_number', '').strip()
            pick.dispatched_at = timezone.now()
            pick.save(update_fields=['status', 'courier_name', 'tracking_number', 'dispatched_at'])
            messages.success(request, "Pick list dispatched.")

        return redirect('wms:picklist_detail', slug=slug, pick_id=pick_id)

    items = pick.items.all()
    bins = StorageBin.objects.filter(zone__business=biz).select_related('zone')
    return render(request, 'wms/picklist_detail.html', {
        'biz': biz,
        'pick': pick,
        'items': items,
        'bins': bins,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })
