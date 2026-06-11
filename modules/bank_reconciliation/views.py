from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request, slug):
    return render(request, 'modules/bank_reconciliation/dashboard.html', {'slug': slug})
