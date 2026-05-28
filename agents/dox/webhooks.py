from agents.dox.engine import DoxEngine, PermissionRequired
from agents.dox.models import DocProject, DocPage
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Dox."""
    engine = DoxEngine()

    if event_type == 'page_requested':
        project_name = payload.get('project_name', 'General')
        project, _ = DocProject.objects.get_or_create(
            business=instance.business,
            name=project_name,
            defaults={'doc_type': payload.get('doc_type', 'wiki'), 'description': 'Auto-created via webhook'}
        )

        page = DocPage.objects.create(
            project=project,
            title=payload.get('title', 'Untitled Page'),
            section=payload.get('section', 'General'),
            content='',
            status='draft'
        )

        try:
            content = engine.generate_page(project, page, instance=instance)
            page.content = content
            page.ai_generated = True
            page.status = 'published'
            page.save(update_fields=['content', 'ai_generated', 'status'])
        except PermissionRequired as pr:
            if "content" in locals():
                page.content = content
                page.save(update_fields=['content'])
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
