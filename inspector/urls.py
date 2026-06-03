from django.urls import path
from . import views

app_name = 'inspector'

urlpatterns = [
    path('check/', views.CheckActionView.as_view(), name='check-action'),
    path('audit-log/', views.AuditLogListView.as_view(), name='audit-log'),
    path('incidents/', views.IncidentListView.as_view(), name='incidents-list'),
    path('incidents/<int:pk>/resolve/', views.ResolveIncidentView.as_view(), name='resolve-incident'),
    path('escalations/pending/', views.EscalationsListView.as_view(), name='escalations-pending'),
    path('escalations/<int:pk>/decide/', views.DecideEscalationView.as_view(), name='decide-escalation'),
    path('rules/', views.RulesListView.as_view(), name='rules-list'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('health/', views.HealthView.as_view(), name='health'),
]
