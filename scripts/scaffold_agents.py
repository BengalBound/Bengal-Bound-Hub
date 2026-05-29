import os
import re

AGENTS_DIR = r"d:\Bengal bound\dev-backoffice\agents"

# Agents we already fully implemented manually
EXCLUDED_AGENTS = ['aria']

def scaffold():
    agents = [
        d for d in os.listdir(AGENTS_DIR)
        if os.path.isdir(os.path.join(AGENTS_DIR, d))
        and os.path.isfile(os.path.join(AGENTS_DIR, d, 'apps.py'))
        and d not in EXCLUDED_AGENTS
    ]

    for agent in agents:
        agent_dir = os.path.join(AGENTS_DIR, agent)

        # 1. Write signals.py
        signals_code = f"""from django.db.models.signals import post_save
from django.dispatch import receiver
from workspace_admin.models import HiredAIEmployee
from agents.models import AgentInstance, AgentCatalog

@receiver(post_save, sender=HiredAIEmployee)
def provision_{agent.replace('-', '_')}_instance(sender, instance, created, **kwargs):
    if not getattr(instance, 'agent_catalog', None) or instance.agent_catalog.slug != '{agent}':
        return
    if instance.is_active:
        business = instance.employer.owned_businesses.first()
        if not business:
            return
            
        obj, is_new = AgentInstance.objects.get_or_create(
            business=business,  # tenant link
            catalog=instance.agent_catalog,
            defaults={{'hired_employee': instance, 'status': 'idle'}}
        )
        if not is_new and obj.status == 'offline':
            obj.status = 'idle'
            obj.save(update_fields=['status'])
    else:
        AgentInstance.objects.filter(hired_employee=instance).update(status='offline')
"""
        with open(os.path.join(agent_dir, 'signals.py'), 'w', encoding='utf-8') as f:
            f.write(signals_code)

        # 2. Patch apps.py
        apps_path = os.path.join(agent_dir, 'apps.py')
        with open(apps_path, 'r', encoding='utf-8') as f:
            apps_content = f.read()

        if "def ready(self):" not in apps_content:
            ready_method = f"\n    def ready(self):\n        import agents.{agent}.signals  # noqa\n"
            apps_content += ready_method
            with open(apps_path, 'w', encoding='utf-8') as f:
                f.write(apps_content)

        # 3. Create basic admin.py
        # We don't know the exact domain models for every agent, so we'll just write a base admin
        # that imports standard django stuff and sets up inlines if they ever register a model.
        # It's better if we scan models.py to register them automatically.
        models_path = os.path.join(agent_dir, 'models.py')
        models_list = []
        if os.path.exists(models_path):
            with open(models_path, 'r', encoding='utf-8') as f:
                models_content = f.read()
                # find class Name(models.Model) or class Name(BaseModel)
                matches = re.findall(r'class\s+([A-Za-z0-9_]+)\((?:models\.Model|BaseModel)\):', models_content)
                for m in matches:
                    models_list.append(m)

        admin_code = "from django.contrib import admin\n"
        if models_list:
            admin_code += f"from .models import {', '.join(models_list)}\n\n"
            for model in models_list:
                admin_code += f"@admin.register({model})\nclass {model}Admin(admin.ModelAdmin):\n    pass\n\n"

        # We don't add AgentLogInline here directly because that's on AgentInstance (which is in agents/admin.py).
        # Wait, the plan said "Every agent admin includes AgentLogInline and AgentPermissionRequestInline".
        # But those are FK to AgentInstance, not to the domain models! So the plan probably meant
        # that the global agent admin has them, or the domain models don't have those inlines directly.
        # Actually, in the Aria pilot, I correctly registered the inlines in agents/admin.py instead of aria/admin.py.
        # So we just register the domain models here.

        if models_list:
            with open(os.path.join(agent_dir, 'admin.py'), 'w', encoding='utf-8') as f:
                f.write(admin_code)
        else:
            # No models, just create empty admin.py
            with open(os.path.join(agent_dir, 'admin.py'), 'w', encoding='utf-8') as f:
                f.write("# No domain models to register\n")

    print(f"Scaffolded {len(agents)} agents.")

if __name__ == '__main__':
    scaffold()
