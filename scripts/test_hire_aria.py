import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bengalbound_core.settings.development")
django.setup()

from workspace_admin.models import HiredAIEmployee, AIEmployeeTier
from hub.models import BusinessInstance
from django.contrib.auth import get_user_model
from agents.models import AgentCatalog, AgentInstance

User = get_user_model()

def prepare_workforce():
    # 1. Get or create a test business owner
    user, _ = User.objects.get_or_create(email="testowner@example.com", defaults={"username": "testowner"})

    # 2. Get or create a test business
    business, _ = BusinessInstance.objects.get_or_create(
        name="Test Business",
        slug="test-business",
        defaults={"owner": user}
    )

    # 3. Get Aria catalog
    aria_catalog = AgentCatalog.objects.filter(slug='aria').first()
    if not aria_catalog:
        print("Aria not found in catalog. Run seed_agents first.")
        return

    # 4. Get or create a tier
    tier, _ = AIEmployeeTier.objects.get_or_create(name='entry', defaults={'description': 'Entry Tier'})

    # 5. Hire Aria
    hired, created = HiredAIEmployee.objects.get_or_create(
        employer=user,
        agent_catalog=aria_catalog,
        defaults={
            'tier': tier,
            'ai_name': "Aria",
            'is_active': True
        }
    )

    if created:
        print(f"Hired AI Employee {hired.ai_name} created.")
    else:
        print(f"Hired AI Employee {hired.ai_name} already exists.")
        # Ensure active
        if not hired.is_active:
            hired.is_active = True
            hired.save()

    # 6. Verify signal worked
    instance = AgentInstance.objects.filter(hired_employee=hired).first()
    if instance:
        print(f"Success! AgentInstance for Aria was auto-provisioned (Status: {instance.status})")
    else:
        print("Failure: AgentInstance was not auto-provisioned. Signal might be disconnected.")

if __name__ == "__main__":
    prepare_workforce()
