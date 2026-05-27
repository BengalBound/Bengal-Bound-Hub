from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from hub.views import _get_business_for_user
from hub.access import get_access_level
from .models import ProcessMap, ProcessStep, ProcessFlow, ProcessDocument, SimulationRun


def _pm_check(slug, user, min_level=2):
    biz = _get_business_for_user(slug, user)
    if not biz:
        return None, HttpResponseForbidden()
    if get_access_level(biz, user) < min_level:
        return None, HttpResponseForbidden()
    return biz, None


@login_required(login_url='/accounts/login/')
def pm_home(request, slug):
    biz, err = _pm_check(slug, request.user)
    if err:
        return err

    maps = ProcessMap.objects.filter(business=biz).select_related('owner')
    status_counts = {}
    for s, _ in ProcessMap.STATUS:
        status_counts[s] = maps.filter(status=s).count()

    return render(request, 'process_mapper/home.html', {
        'biz': biz,
        'maps': maps[:10],
        'status_counts': status_counts,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def process_list(request, slug):
    biz, err = _pm_check(slug, request.user)
    if err:
        return err

    level = get_access_level(biz, request.user)
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '').strip()

    maps = ProcessMap.objects.filter(business=biz).select_related('owner')
    if status_filter:
        maps = maps.filter(status=status_filter)
    if search:
        maps = maps.filter(name__icontains=search) | ProcessMap.objects.filter(
            business=biz, tags__icontains=search)

    return render(request, 'process_mapper/process_list.html', {
        'biz': biz,
        'maps': maps,
        'statuses': ProcessMap.STATUS,
        'status_filter': status_filter,
        'search': search,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def process_create(request, slug):
    biz, err = _pm_check(slug, request.user, min_level=3)
    if err:
        return err

    if request.method == 'POST':
        from hub.models import BusinessEmployee
        owner_id = request.POST.get('owner_id', '')
        pm = ProcessMap.objects.create(
            business=biz,
            name=request.POST.get('name', '').strip(),
            description=request.POST.get('description', '').strip(),
            version=request.POST.get('version', '1.0').strip(),
            status='draft',
            owner_id=int(owner_id) if owner_id else None,
            tags=request.POST.get('tags', '').strip(),
            created_by=request.user,
        )
        messages.success(request, f"Process map '{pm.name}' created.")
        return redirect('process_mapper:process_detail', slug=slug, map_id=pm.pk)

    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    return render(request, 'process_mapper/process_form.html', {
        'biz': biz,
        'employees': employees,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def process_detail(request, slug, map_id):
    biz, err = _pm_check(slug, request.user)
    if err:
        return err

    pm = get_object_or_404(ProcessMap, pk=map_id, business=biz)
    level = get_access_level(biz, request.user)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'add_step' and level >= 3:
            emp_id = request.POST.get('responsible_employee_id', '')
            order = pm.steps.count() + 1
            ProcessStep.objects.create(
                process_map=pm,
                name=request.POST.get('name', '').strip(),
                step_type=request.POST.get('step_type', 'task'),
                description=request.POST.get('description', '').strip(),
                responsible_role=request.POST.get('responsible_role', '').strip(),
                responsible_employee_id=int(emp_id) if emp_id else None,
                duration_estimate=request.POST.get('duration_estimate', '').strip(),
                inputs=request.POST.get('inputs', '').strip(),
                outputs=request.POST.get('outputs', '').strip(),
                tools_used=request.POST.get('tools_used', '').strip(),
                sla=request.POST.get('sla', '').strip(),
                order=order,
            )
            messages.success(request, "Step added.")

        elif action == 'delete_step' and level >= 4:
            step_id = request.POST.get('step_id', '')
            if step_id:
                ProcessStep.objects.filter(pk=int(step_id), process_map=pm).delete()

        elif action == 'add_flow' and level >= 3:
            from_id = request.POST.get('from_step_id', '')
            to_id = request.POST.get('to_step_id', '')
            if from_id and to_id:
                ProcessFlow.objects.get_or_create(
                    process_map=pm,
                    from_step_id=int(from_id),
                    to_step_id=int(to_id),
                    defaults={
                        'flow_type': request.POST.get('flow_type', 'sequence'),
                        'label': request.POST.get('label', '').strip(),
                    }
                )
                messages.success(request, "Flow connection added.")

        elif action == 'update_status' and level >= 4:
            pm.status = request.POST.get('status', pm.status)
            pm.save(update_fields=['status'])
            messages.success(request, f"Status updated to {pm.get_status_display()}.")

        elif action == 'run_simulation' and level >= 3:
            step_id = request.POST.get('bottleneck_step_id', '')
            SimulationRun.objects.create(
                process_map=pm,
                label=request.POST.get('sim_label', '').strip(),
                assumptions=request.POST.get('assumptions', '').strip(),
                results_summary=request.POST.get('results_summary', '').strip(),
                bottleneck_step_id=int(step_id) if step_id else None,
                throughput_per_day=request.POST.get('throughput_per_day', '') or None,
                avg_cycle_time=request.POST.get('avg_cycle_time', '').strip(),
                run_by=request.user,
            )
            messages.success(request, "Simulation run recorded.")

        elif action == 'add_document' and level >= 3:
            doc = ProcessDocument(
                process_map=pm,
                title=request.POST.get('doc_title', '').strip(),
                url=request.POST.get('doc_url', '').strip(),
                description=request.POST.get('doc_description', '').strip(),
                uploaded_by=request.user,
            )
            if 'doc_file' in request.FILES:
                doc.file = request.FILES['doc_file']
            doc.save()
            messages.success(request, "Document attached.")

        return redirect('process_mapper:process_detail', slug=slug, map_id=map_id)

    steps = pm.steps.all()
    flows = pm.flows.select_related('from_step', 'to_step')
    documents = pm.documents.all()
    simulations = pm.simulations.all()

    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'process_mapper/process_detail.html', {
        'biz': biz,
        'pm': pm,
        'steps': steps,
        'flows': flows,
        'documents': documents,
        'simulations': simulations,
        'employees': employees,
        'step_types': ProcessStep.STEP_TYPES,
        'flow_types': ProcessFlow.FLOW_TYPES,
        'statuses': ProcessMap.STATUS,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })
