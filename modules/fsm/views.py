from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from hub.models import BusinessInstance, BusinessEmployee
from .models import Job, JobQuote, CustomerSignature, VanInventory

def get_business_and_employee(request, slug):
    business = get_object_or_404(BusinessInstance, slug=slug)
    employee = get_object_or_404(BusinessEmployee, business=business, user=request.user)
    return business, employee

@login_required
def fsm_dashboard(request, slug):
    business, employee = get_business_and_employee(request, slug)
    jobs = Job.objects.filter(business=business).order_by('scheduled_datetime')
    return render(request, 'fsm/dashboard.html', {
        'business': business,
        'employee': employee,
        'jobs': jobs,
    })

@login_required
def map_dispatch(request, slug):
    business, employee = get_business_and_employee(request, slug)
    jobs = Job.objects.filter(business=business).exclude(latitude__isnull=True, longitude__isnull=True)
    return render(request, 'fsm/map_dispatch.html', {
        'business': business,
        'employee': employee,
        'jobs': jobs,
    })

@login_required
def quote_builder(request, slug, job_id):
    business, employee = get_business_and_employee(request, slug)
    job = get_object_or_404(Job, id=job_id, business=business)
    # Basic logic for demonstration; would handle POST to create items
    quote = job.quotes.first()
    if not quote:
        quote = JobQuote.objects.create(job=job)
    return render(request, 'fsm/quote_builder.html', {
        'business': business,
        'employee': employee,
        'job': job,
        'quote': quote,
    })

@login_required
def signature_capture(request, slug, job_id):
    business, employee = get_business_and_employee(request, slug)
    job = get_object_or_404(Job, id=job_id, business=business)
    
    if request.method == 'POST':
        signature_data = request.POST.get('signature_data')
        signed_by_name = request.POST.get('signed_by_name')
        if signature_data and signed_by_name:
            CustomerSignature.objects.create(
                job=job,
                signature_data=signature_data,
                signed_by_name=signed_by_name
            )
            job.status = 'completed'
            job.save()
            return redirect('fsm:dashboard', slug=slug)
            
    return render(request, 'fsm/signature.html', {
        'business': business,
        'employee': employee,
        'job': job,
    })

@login_required
def inventory_sync(request, slug):
    business, employee = get_business_and_employee(request, slug)
    
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        new_quantity = request.POST.get('quantity')
        if item_id and new_quantity is not None:
            inventory_item = get_object_or_404(VanInventory, id=item_id, technician=employee, business=business)
            inventory_item.quantity = int(new_quantity)
            inventory_item.save()
            return redirect('fsm:inventory_sync', slug=slug)
            
    inventory_items = VanInventory.objects.filter(business=business, technician=employee)
    
    return render(request, 'fsm/inventory_sync.html', {
        'business': business,
        'employee': employee,
        'inventory_items': inventory_items,
    })
