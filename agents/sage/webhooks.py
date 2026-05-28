from agents.sage.engine import SageEngine, PermissionRequired
from agents.sage.models import LegalDocument, Clause
from agents.models import AgentInstance, AgentPermissionRequest
from django.utils import timezone

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Sage."""
    engine = SageEngine()
    
    if event_type == 'document_uploaded':
        # E.g. from DocuSign or a contract management tool
        document, created = LegalDocument.objects.get_or_create(
            business=instance.business,
            name=payload.get('document_name', 'Unknown Document'),
            defaults={
                'document_type': payload.get('document_type', 'contract'),
                'raw_text': payload.get('raw_text', ''),
                'status': 'queued'
            }
        )
        
        if created and document.raw_text:
            try:
                document.status = 'reviewing'
                document.save(update_fields=['status'])
                
                result = engine.review_document(document, instance=instance)
                
                document.overall_risk = result.get("overall_risk", 50)
                document.risk_label = result.get("risk_label", "medium")
                document.executive_summary = result.get("executive_summary", "")
                document.status = "completed"
                document.reviewed_at = timezone.now()
                document.save(update_fields=["overall_risk", "risk_label", "executive_summary", "status", "reviewed_at"])

                for clause_data in result.get("clauses", []):
                    Clause.objects.create(
                        business=document.business,
                        document=document,
                        clause_title=clause_data.get("clause_title", ""),
                        original_text=clause_data.get("original_text", ""),
                        plain_english=clause_data.get("plain_english", ""),
                        risk_level=clause_data.get("risk_level", "safe"),
                        risk_score=clause_data.get("risk_score", 0),
                        negotiation_suggestion=clause_data.get("negotiation_suggestion", ""),
                    )
            except PermissionRequired as pr:
                # Save partial state
                if "result" in locals():
                    document.overall_risk = result.get("overall_risk", 50)
                    document.risk_label = result.get("risk_label", "medium")
                    document.executive_summary = result.get("executive_summary", "")
                    document.status = "completed"
                    document.reviewed_at = timezone.now()
                    document.save(update_fields=["overall_risk", "risk_label", "executive_summary", "status", "reviewed_at"])
                
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as e:
                document.status = 'failed'
                document.save(update_fields=['status'])
