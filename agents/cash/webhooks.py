from django.utils import timezone
import dateutil.parser
from agents.cash.engine import CashEngine, PermissionRequired
from agents.cash.models import Employee
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Cash."""
    engine = CashEngine()
    
    if event_type == 'employee_synced':
        try:
            join_date = dateutil.parser.isoparse(payload.get('join_date')).date()
        except (ValueError, TypeError):
            join_date = timezone.now().date()

        employee, _ = Employee.objects.update_or_create(
            business=instance.business,
            name=payload.get('name', 'Unknown'),
            defaults={
                'department': payload.get('department', 'General'),
                'basic_salary': payload.get('basic_salary', 0.0),
                'house_rent': payload.get('house_rent', 0.0),
                'medical': payload.get('medical', 0.0),
                'pf_enrolled': payload.get('pf_enrolled', False),
                'tin_number': payload.get('tin_number', ''),
                'join_date': join_date
            }
        )
        
        try:
            # We can optionally run a compliance check on sync
            res = engine.compliance_check(employee, instance=instance)
        except PermissionRequired as pr:
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
