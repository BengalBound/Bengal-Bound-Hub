import sys

filepath = r'g:\[Bengal Bound]\BengalBound-HUB\templates\workspace_admin\base_admin.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'href="/" class="text-decoration': 'href="{% url \'workspace_admin:dashboard\' %}" class="text-decoration',
    'href="/" class="nav-link': 'href="{% url \'workspace_admin:dashboard\' %}" class="nav-link',
    'href="/ai-oversight/"': 'href="{% url \'workspace_admin:ai_oversight\' %}"',
    'href="/serea-config/"': 'href="{% url \'workspace_admin:serea_config\' %}"',
    'href="/ai-tiers/"': 'href="{% url \'workspace_admin:ai_tiers\' %}"',
    'href="/projects/"': 'href="{% url \'workspace_admin:project_control\' %}"',
    'href="/monitoring/"': 'href="{% url \'workspace_admin:project_monitoring\' %}"',
    'href="/crm/"': 'href="{% url \'workspace_admin:crm_support\' %}"',
    'href="/data/"': 'href="{% url \'workspace_admin:data_traffic\' %}"',
    'href="/marketing/"': 'href="{% url \'workspace_admin:marketing\' %}"',
    'href="/cms/"': 'href="{% url \'workspace_admin:cms_control\' %}"',
    'href="/forum/"': 'href="{% url \'workspace_admin:forum_management\' %}"'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated base_admin.html successfully.')
