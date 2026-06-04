import pytest
from django.utils import timezone
from serea.models import (
    SereaAgent, ContentQueue, SereaTask, EngagementLog, CampaignTracker
)
from serea.logic import (
    trigger_permission_request, create_social_post, list_scheduled_posts,
    check_moderation_stats, generate_report, save_report, save_client_instruction,
    check_onboarding_status, get_business_knowledge, get_my_tasks, create_task,
    update_task, mark_onboarding_complete, log_engagement_action, create_campaign
)
import json

@pytest.mark.django_db
class TestSereaToolsAdvanced:
    def test_get_my_tasks(self, agent_setup):
        user, agent = agent_setup
        
        # Test empty tasks
        res = get_my_tasks.invoke({"agent_id": str(agent.id)})
        assert "No tasks assigned yet" in res
        
        # Create some tasks
        SereaTask.objects.create(agent=agent, title="Task 1", priority="high", status="in_progress", progress_notes="Working on it")
        SereaTask.objects.create(agent=agent, title="Task 2", priority="normal", status="done")
        
        res = get_my_tasks.invoke({"agent_id": str(agent.id)})
        assert "Active tasks" in res
        assert "Task 1" in res
        assert "Completed (1 tasks)" in res
        
        # Test invalid agent ID
        res = get_my_tasks.invoke({"agent_id": "9999"})
        assert "ERROR" in res

    def test_create_task(self, agent_setup):
        user, agent = agent_setup
        res = create_task.invoke({"agent_id": str(agent.id), "title": "New Task", "description": "Desc", "priority": "high"})
        assert "Task created!" in res
        assert SereaTask.objects.filter(agent=agent, title="New Task").exists()

        # Test invalid agent
        res = create_task.invoke({"agent_id": "9999", "title": "New Task"})
        assert "ERROR" in res

    def test_update_task(self, agent_setup):
        user, agent = agent_setup
        task = SereaTask.objects.create(agent=agent, title="Task 1", priority="high", status="in_progress")
        
        res = update_task.invoke({"agent_id": str(agent.id), "task_id": str(task.id), "status": "done", "notes": "Done it", "result": "Success"})
        assert "updated" in res
        task.refresh_from_db()
        assert task.status == "done"
        assert task.progress_notes == "Done it"
        assert task.result == "Success"
        assert task.completed_at is not None

        # Test invalid agent/task
        res = update_task.invoke({"agent_id": str(agent.id), "task_id": "9999", "status": "done"})
        assert "ERROR" in res

    def test_check_onboarding_status(self, agent_setup):
        user, agent = agent_setup
        res = check_onboarding_status.invoke({"agent_id": str(agent.id)})
        data = json.loads(res)
        assert data["onboarding_complete"] is False

    def test_mark_onboarding_complete(self, agent_setup):
        user, agent = agent_setup
        
        # Should fail if no platforms or content
        res = mark_onboarding_complete.invoke({"agent_id": str(agent.id)})
        assert "Cannot complete onboarding" in res
        
        # Add platform and content
        agent.social_accounts.create(platform='facebook', is_active=True, extra_credentials={"token": "123"})
        agent.content_files.create(title="Brand", content_type='brand_guide', is_active=True)
        
        res = mark_onboarding_complete.invoke({"agent_id": str(agent.id)})
        assert "Onboarding marked as complete" in res
        agent.refresh_from_db()
        assert agent.onboarding_complete is True

    def test_get_business_knowledge(self, agent_setup):
        user, agent = agent_setup
        
        # No knowledge
        res = get_business_knowledge.invoke({"agent_id": str(agent.id)})
        assert "No business content" in res
        
        # Add knowledge
        agent.content_files.create(title="Brand Guide", content_type='brand_guide', parsed_content="We are friendly", is_active=True)
        agent.content_files.create(title="Pricing", content_type='faq', parsed_content="10 dollars", is_active=True)
        
        res = get_business_knowledge.invoke({"agent_id": str(agent.id), "query": "Pricing"})
        assert "10 dollars" in res
        assert "friendly" not in res
        
        # No match query
        res = get_business_knowledge.invoke({"agent_id": str(agent.id), "query": "Unknown"})
        assert "No content matched" in res

    def test_log_engagement_action(self, agent_setup):
        user, agent = agent_setup
        res = log_engagement_action.invoke({
            "agent_id": str(agent.id), 
            "platform": "facebook", 
            "action": "like", 
            "target_account": "user1"
        })
        assert "Engagement logged" in res
        assert EngagementLog.objects.filter(agent=agent, action="like").exists()

    def test_create_campaign(self, agent_setup):
        user, agent = agent_setup
        res = create_campaign.invoke({
            "agent_id": str(agent.id),
            "name": "Summer Sale",
            "platforms": "facebook, instagram"
        })
        assert "Campaign created!" in res
        assert CampaignTracker.objects.filter(agent=agent, name="Summer Sale").exists()
