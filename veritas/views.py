from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import ClientApplication, KYBDocument

@staff_member_required
def kyb_list(request):
    applications = ClientApplication.objects.all().order_by('-submitted_at')
    return render(request, 'veritas/kyb_list.html', {'applications': applications})

@staff_member_required
def kyb_detail(request, app_id):
    app = get_object_or_404(ClientApplication, id=app_id)
    documents = app.documents.all()
    sanctions = app.sanction_checks.all()
    agreements = app.agreements.all()
    return render(request, 'veritas/kyb_detail.html', {
        'app': app,
        'documents': documents,
        'sanctions': sanctions,
        'agreements': agreements
    })

@staff_member_required
def kyb_approve(request, app_id):
    app = get_object_or_404(ClientApplication, id=app_id)
    if request.method == 'POST':
        app.status = 'approved'
        app.save()
        messages.success(request, f"Application for {app.company_name} approved successfully.")
    return redirect('console_admin:veritas:kyb_list')

@staff_member_required
def kyb_reject(request, app_id):
    app = get_object_or_404(ClientApplication, id=app_id)
    if request.method == 'POST':
        app.status = 'rejected'
        app.save()
        messages.error(request, f"Application for {app.company_name} rejected.")
    return redirect('console_admin:veritas:kyb_list')
