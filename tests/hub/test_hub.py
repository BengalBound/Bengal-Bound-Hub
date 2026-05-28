from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class BusinessInstanceTests(TestCase):
    """Tests for BusinessInstance multi-tenancy."""

    # TODO: test business creation, slug generation
    # TODO: test BusinessEmployee access levels
    # TODO: test IP-locking (BusinessAccessMiddleware)


class ModuleCatalogTests(TestCase):
    """Tests for module marketplace (seed_modules command)."""

    def test_seed_modules_importable(self):
        from hub.management.commands.seed_modules import Command
        self.assertIsNotNone(Command)

    # TODO: test seed_modules creates all 83 ModuleCatalog entries
    # TODO: test TenantModule activation/deactivation


class AgentCatalogTests(TestCase):
    """Tests for agent marketplace (seed_agents command)."""

    def test_seed_agents_importable(self):
        from agents.management.commands.seed_agents import Command
        self.assertIsNotNone(Command)

    # TODO: test seed_agents creates all 33 AgentCatalog entries
    # TODO: test tier_required enforcement


class SubscriptionTests(TestCase):
    """Tests for business subscription tiers."""
    pass  # TODO
