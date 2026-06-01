"""
Generic agent API URL patterns — included once per agent slug in the main urls.py.
"""
from django.urls import path
from .api_views import (
    AgentStatusView,
    AgentLogsView,
    AgentRunView,
    AgentApprovalsView,
    AgentDecideView,
)

urlpatterns = [
    path('status/',                          AgentStatusView.as_view(),   name='agent_status'),
    path('logs/',                            AgentLogsView.as_view(),     name='agent_logs'),
    path('run/',                             AgentRunView.as_view(),      name='agent_run'),
    path('approvals/',                       AgentApprovalsView.as_view(),name='agent_approvals'),
    path('approvals/<int:pk>/decide/',       AgentDecideView.as_view(),   name='agent_decide'),
]
