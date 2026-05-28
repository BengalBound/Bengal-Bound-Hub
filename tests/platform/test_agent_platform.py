from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class AgentInstanceTests(TestCase):
    """Tests for AgentInstance lifecycle — provision, activate, deactivate."""

    def test_agent_catalog_import(self):
        from agents.models import AgentCatalog
        self.assertIsNotNone(AgentCatalog)

    def test_agent_instance_import(self):
        from agents.models import AgentInstance
        self.assertIsNotNone(AgentInstance)

    # TODO: test signal provisioning (HiredAIEmployee → AgentInstance)
    # TODO: test AgentInstance.status transitions (idle → working → waiting → idle)


class AgentPermissionFlowTests(TestCase):
    """Tests for the human-in-the-loop permission request flow."""

    # TODO: test PermissionRequired raised → AgentPermissionRequest created
    # TODO: test permission_respond view (approve and deny paths)
    # TODO: test resume_after_permission task resets status to idle


class AgentLogTests(TestCase):
    """Tests for AgentLog audit trail."""

    # TODO: test AgentLog created after engine action
    # TODO: test log.outcome values (success, failed, escalated, pending)


class InboundWebhookTests(TestCase):
    """Tests for the universal inbound webhook receiver."""

    # TODO: test valid HMAC → routes to agent webhooks.handle_event()
    # TODO: test invalid HMAC → 401 response
    # TODO: test event_count increments on each POST


class AgentMemoryTests(TestCase):
    """Tests for AgentMemory long-term context."""

    # TODO: test create, retrieve, expire memory records


class AgentIntegrationTests(TestCase):
    """Tests for encrypted AgentIntegration credentials."""

    # TODO: test EncryptedTextField encrypts on write, decrypts on read
    # TODO: test SlackAdapter.send_notification
    # TODO: test EmailAdapter.send_permission_request
