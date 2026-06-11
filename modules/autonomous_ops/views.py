from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request, slug):
    return render(request, 'modules/autonomous_ops/dashboard.html', {'slug': slug})
