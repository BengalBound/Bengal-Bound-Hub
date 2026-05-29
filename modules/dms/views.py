from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from hub.views import _get_business_for_user
from hub.access import get_access_level
from .models import VehicleStock, VehiclePhoto, VehicleDeal, TradeIn, DealNote


def _dms_check(slug, user, min_level=2):
    biz = _get_business_for_user(slug, user)
    if not biz:
        return None, HttpResponseForbidden()
    if get_access_level(biz, user) < min_level:
        return None, HttpResponseForbidden()
    return biz, None


def _next_stock_number(business):
    last = VehicleStock.objects.filter(business=business).order_by('-pk').first()
    num = int(last.stock_number.lstrip('S')) + 1 if last else 1
    return f"S{str(num).zfill(5)}"


def _next_deal_number(business):
    last = VehicleDeal.objects.filter(business=business).order_by('-pk').first()
    num = int(last.deal_number) + 1 if last else 1
    return str(num).zfill(5)


@login_required(login_url='/accounts/login/')
def dms_dashboard(request, slug):
    biz, err = _dms_check(slug, request.user)
    if err:
        return err

    stock_counts = {}
    for s, _ in VehicleStock.STATUS:
        stock_counts[s] = VehicleStock.objects.filter(business=biz, status=s).count()

    deal_counts = {}
    for s, _ in VehicleDeal.STAGES:
        deal_counts[s] = VehicleDeal.objects.filter(business=biz, stage=s).count()

    recent_stock = VehicleStock.objects.filter(business=biz).select_related()[:8]
    active_deals = VehicleDeal.objects.filter(
        business=biz,
        stage__in=['enquiry', 'test_drive', 'negotiation', 'agreed', 'finance', 'documentation']
    ).select_related('vehicle', 'salesperson')[:10]

    return render(request, 'dms/dashboard.html', {
        'biz': biz,
        'stock_counts': stock_counts,
        'deal_counts': deal_counts,
        'recent_stock': recent_stock,
        'active_deals': active_deals,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def vehicle_list(request, slug):
    biz, err = _dms_check(slug, request.user)
    if err:
        return err

    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('stock_type', '')
    search = request.GET.get('q', '').strip()

    vehicles = VehicleStock.objects.filter(business=biz)
    if status_filter:
        vehicles = vehicles.filter(status=status_filter)
    if type_filter:
        vehicles = vehicles.filter(stock_type=type_filter)
    if search:
        vehicles = vehicles.filter(make__icontains=search) | VehicleStock.objects.filter(
            business=biz, model__icontains=search) | VehicleStock.objects.filter(
            business=biz, reg_number__icontains=search) | VehicleStock.objects.filter(
            business=biz, stock_number__icontains=search)

    return render(request, 'dms/vehicle_list.html', {
        'biz': biz,
        'vehicles': vehicles,
        'statuses': VehicleStock.STATUS,
        'stock_types': VehicleStock.STOCK_TYPE,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search': search,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def vehicle_add(request, slug):
    biz, err = _dms_check(slug, request.user, min_level=3)
    if err:
        return err

    if request.method == 'POST':
        vehicle = VehicleStock.objects.create(
            business=biz,
            stock_number=_next_stock_number(biz),
            make=request.POST.get('make', '').strip(),
            model=request.POST.get('model', '').strip(),
            variant=request.POST.get('variant', '').strip(),
            year=request.POST.get('year', 0),
            colour=request.POST.get('colour', '').strip(),
            interior_colour=request.POST.get('interior_colour', '').strip(),
            vin=request.POST.get('vin', '').strip(),
            reg_number=request.POST.get('reg_number', '').strip().upper(),
            engine_size=request.POST.get('engine_size', '').strip(),
            transmission=request.POST.get('transmission', 'auto'),
            fuel_type=request.POST.get('fuel_type', 'petrol'),
            body_type=request.POST.get('body_type', '').strip(),
            doors=request.POST.get('doors', '') or None,
            seats=request.POST.get('seats', '') or None,
            mileage=request.POST.get('mileage', '') or None,
            stock_type=request.POST.get('stock_type', 'used'),
            condition=request.POST.get('condition', 'good'),
            status=request.POST.get('status', 'available'),
            location=request.POST.get('location', '').strip(),
            purchase_price=request.POST.get('purchase_price', '') or None,
            asking_price=request.POST.get('asking_price', '') or None,
            reserve_price=request.POST.get('reserve_price', '') or None,
            description=request.POST.get('description', '').strip(),
            features=request.POST.get('features', '').strip(),
            date_acquired=request.POST.get('date_acquired', '') or None,
        )
        if 'main_photo' in request.FILES:
            vehicle.main_photo = request.FILES['main_photo']
            vehicle.save(update_fields=['main_photo'])
        messages.success(request, f"Vehicle {vehicle.stock_number} added to stock.")
        return redirect('dms:vehicle_detail', slug=slug, stock_id=vehicle.pk)

    return render(request, 'dms/vehicle_form.html', {
        'biz': biz,
        'statuses': VehicleStock.STATUS,
        'stock_types': VehicleStock.STOCK_TYPE,
        'conditions': VehicleStock.CONDITION,
        'transmissions': VehicleStock.TRANSMISSION,
        'fuels': VehicleStock.FUEL,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def vehicle_detail(request, slug, stock_id):
    biz, err = _dms_check(slug, request.user)
    if err:
        return err

    vehicle = get_object_or_404(VehicleStock, pk=stock_id, business=biz)
    level = get_access_level(biz, request.user)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'status' and level >= 3:
            vehicle.status = request.POST.get('status', vehicle.status)
            vehicle.save(update_fields=['status'])
            messages.success(request, "Stock status updated.")

        elif action == 'update' and level >= 3:
            vehicle.asking_price = request.POST.get('asking_price', '') or vehicle.asking_price
            vehicle.reserve_price = request.POST.get('reserve_price', '') or vehicle.reserve_price
            vehicle.location = request.POST.get('location', vehicle.location).strip()
            vehicle.description = request.POST.get('description', vehicle.description).strip()
            vehicle.features = request.POST.get('features', vehicle.features).strip()
            vehicle.save(update_fields=['asking_price', 'reserve_price', 'location', 'description', 'features'])
            messages.success(request, "Vehicle details updated.")

        elif action == 'add_photo' and level >= 3:
            if 'photo' in request.FILES:
                VehiclePhoto.objects.create(
                    vehicle=vehicle,
                    photo=request.FILES['photo'],
                    caption=request.POST.get('caption', '').strip(),
                    order=request.POST.get('order', 0),
                )
                messages.success(request, "Photo added.")

        elif action == 'delete_photo' and level >= 4:
            photo_id = request.POST.get('photo_id', '')
            if photo_id:
                VehiclePhoto.objects.filter(pk=int(photo_id), vehicle=vehicle).delete()

        return redirect('dms:vehicle_detail', slug=slug, stock_id=stock_id)

    photos = vehicle.photos.all()
    deals = vehicle.deals.all()

    return render(request, 'dms/vehicle_detail.html', {
        'biz': biz,
        'vehicle': vehicle,
        'photos': photos,
        'deals': deals,
        'statuses': VehicleStock.STATUS,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def deal_list(request, slug):
    biz, err = _dms_check(slug, request.user)
    if err:
        return err

    stage_filter = request.GET.get('stage', '')
    search = request.GET.get('q', '').strip()

    deals = VehicleDeal.objects.filter(business=biz).select_related('vehicle', 'salesperson')
    if stage_filter:
        deals = deals.filter(stage=stage_filter)
    if search:
        deals = deals.filter(customer_name__icontains=search) | VehicleDeal.objects.filter(
            business=biz, vehicle__reg_number__icontains=search) | VehicleDeal.objects.filter(
            business=biz, deal_number__icontains=search)

    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'dms/deal_list.html', {
        'biz': biz,
        'deals': deals,
        'stages': VehicleDeal.STAGES,
        'stage_filter': stage_filter,
        'search': search,
        'employees': employees,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def deal_create(request, slug):
    biz, err = _dms_check(slug, request.user, min_level=3)
    if err:
        return err

    if request.method == 'POST':
        from hub.models import BusinessEmployee
        vehicle_id = request.POST.get('vehicle_id', '')
        salesperson_id = request.POST.get('salesperson_id', '')

        if not vehicle_id:
            messages.error(request, "Please select a vehicle.")
            return redirect('dms:deal_create', slug=slug)

        vehicle = get_object_or_404(VehicleStock, pk=int(vehicle_id), business=biz)

        deal = VehicleDeal.objects.create(
            business=biz,
            deal_number=_next_deal_number(biz),
            vehicle=vehicle,
            stage='enquiry',
            customer_name=request.POST.get('customer_name', '').strip(),
            customer_phone=request.POST.get('customer_phone', '').strip(),
            customer_email=request.POST.get('customer_email', '').strip(),
            customer_address=request.POST.get('customer_address', '').strip(),
            sale_price=request.POST.get('sale_price', '') or None,
            deposit_amount=request.POST.get('deposit_amount', 0) or 0,
            finance_type=request.POST.get('finance_type', 'cash'),
            finance_provider=request.POST.get('finance_provider', '').strip(),
            finance_amount=request.POST.get('finance_amount', '') or None,
            monthly_repayment=request.POST.get('monthly_repayment', '') or None,
            loan_term_months=request.POST.get('loan_term_months', '') or None,
            salesperson_id=int(salesperson_id) if salesperson_id else None,
            notes=request.POST.get('notes', '').strip(),
            created_by=request.user,
        )

        # Trade-in
        ti_make = request.POST.get('ti_make', '').strip()
        if ti_make:
            TradeIn.objects.create(
                deal=deal,
                make=ti_make,
                model=request.POST.get('ti_model', '').strip(),
                year=request.POST.get('ti_year', '') or None,
                reg_number=request.POST.get('ti_reg', '').strip().upper(),
                mileage=request.POST.get('ti_mileage', '') or None,
                condition=request.POST.get('ti_condition', 'good'),
                offered_price=request.POST.get('ti_offered', '') or None,
            )

        messages.success(request, f"Deal DEAL-{deal.deal_number} created.")
        return redirect('dms:deal_detail', slug=slug, deal_id=deal.pk)

    from hub.models import BusinessEmployee
    vehicles = VehicleStock.objects.filter(business=biz, status='available')
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'dms/deal_form.html', {
        'biz': biz,
        'vehicles': vehicles,
        'employees': employees,
        'finance_types': VehicleDeal.FINANCE_TYPES,
        'conditions': VehicleStock.CONDITION,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def deal_detail(request, slug, deal_id):
    biz, err = _dms_check(slug, request.user)
    if err:
        return err

    deal = get_object_or_404(VehicleDeal, pk=deal_id, business=biz)
    level = get_access_level(biz, request.user)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'stage' and level >= 3:
            deal.stage = request.POST.get('stage', deal.stage)
            if deal.stage == 'delivered' and not deal.delivery_date:
                from datetime import date
                deal.delivery_date = date.today()
                deal.vehicle.status = 'sold'
                deal.vehicle.save(update_fields=['status'])
            deal.save()
            messages.success(request, f"Deal stage updated to {deal.get_stage_display()}.")

        elif action == 'finance' and level >= 3:
            deal.sale_price = request.POST.get('sale_price', '') or deal.sale_price
            deal.deposit_amount = request.POST.get('deposit_amount', deal.deposit_amount) or deal.deposit_amount
            deal.finance_type = request.POST.get('finance_type', deal.finance_type)
            deal.finance_provider = request.POST.get('finance_provider', deal.finance_provider).strip()
            deal.finance_amount = request.POST.get('finance_amount', '') or deal.finance_amount
            deal.monthly_repayment = request.POST.get('monthly_repayment', '') or deal.monthly_repayment
            deal.loan_term_months = request.POST.get('loan_term_months', '') or deal.loan_term_months
            deal.save()
            messages.success(request, "Finance details updated.")

        elif action == 'note' and level >= 2:
            note_text = request.POST.get('note', '').strip()
            if note_text:
                DealNote.objects.create(deal=deal, note=note_text, author=request.user)
                messages.success(request, "Note added.")

        elif action == 'tradein' and level >= 3:
            ti_make = request.POST.get('ti_make', '').strip()
            if ti_make:
                TradeIn.objects.update_or_create(
                    deal=deal,
                    defaults={
                        'make': ti_make,
                        'model': request.POST.get('ti_model', '').strip(),
                        'year': request.POST.get('ti_year', '') or None,
                        'reg_number': request.POST.get('ti_reg', '').strip().upper(),
                        'mileage': request.POST.get('ti_mileage', '') or None,
                        'condition': request.POST.get('ti_condition', 'good'),
                        'offered_price': request.POST.get('ti_offered', '') or None,
                        'accepted_price': request.POST.get('ti_accepted', '') or None,
                        'notes': request.POST.get('ti_notes', '').strip(),
                    }
                )
                messages.success(request, "Trade-in updated.")

        return redirect('dms:deal_detail', slug=slug, deal_id=deal_id)

    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    notes = deal.deal_notes.all()
    trade_in = getattr(deal, 'trade_in', None)

    return render(request, 'dms/deal_detail.html', {
        'biz': biz,
        'deal': deal,
        'notes': notes,
        'trade_in': trade_in,
        'employees': employees,
        'stages': VehicleDeal.STAGES,
        'finance_types': VehicleDeal.FINANCE_TYPES,
        'conditions': VehicleStock.CONDITION,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })
