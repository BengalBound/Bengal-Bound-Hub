from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request, slug):
    return render(request, 'modules/data_ecosystem/dashboard.html', {'slug': slug})
