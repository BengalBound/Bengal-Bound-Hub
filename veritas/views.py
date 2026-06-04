from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import ClientApplication, KYBDocument
from .forms import ClientApplicationForm, KYBDocumentForm

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
        messages.success(request, f"Application for {app.company_legal_name} approved successfully.")
    return redirect('console_admin:veritas:kyb_list')

@staff_member_required
def kyb_reject(request, app_id):
    app = get_object_or_404(ClientApplication, id=app_id)
    if request.method == 'POST':
        app.status = 'rejected'
        app.save()
        messages.error(request, f"Application for {app.company_legal_name} rejected.")
    return redirect('console_admin:veritas:kyb_list')

# User-Facing KYB Views
@login_required
def kyb_apply_user(request):
    # If already submitted/approved, redirect to pending or dashboard
    existing_app = ClientApplication.objects.filter(user=request.user).first()
    if existing_app:
        if existing_app.status == 'approved':
            return redirect('console_admin:dashboard')
        return redirect('veritas_user:kyb_pending')

    if request.method == 'POST':
        app_form = ClientApplicationForm(request.POST)
        doc_form = KYBDocumentForm(request.POST, request.FILES)
        
        if app_form.is_valid() and doc_form.is_valid():
            app = app_form.save(commit=False)
            app.user = request.user
            app.business = getattr(request.user, 'business', None)
            app.status = 'under_review'
            app.save()

            doc = doc_form.save(commit=False)
            doc.application = app
            doc.status = 'uploaded'
            doc.save()

            messages.success(request, "Your application has been submitted for review.")
            return redirect('veritas_user:kyb_pending')
    else:
        app_form = ClientApplicationForm()
        doc_form = KYBDocumentForm()

    return render(request, 'veritas/kyb_apply.html', {
        'app_form': app_form,
        'doc_form': doc_form
    })

@login_required
def kyb_pending_user(request):
    app = ClientApplication.objects.filter(user=request.user).first()
    if not app:
        return redirect('veritas_user:kyb_apply')
    if app.status == 'approved':
        return redirect('console_admin:dashboard')
    
    return render(request, 'veritas/kyb_pending.html', {'app': app})
