from agents.voice_receptionist.engine import VoiceReceptionistEngine, PermissionRequired
from agents.voice_receptionist.models import Call, BusinessProfile
from agents.models import AgentInstance, AgentPermissionRequest
from django.utils import timezone

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Voice Receptionist."""
    engine = VoiceReceptionistEngine()
    
    if event_type == 'call_ended':
        transcript = payload.get('transcript', '')
        
        try:
            business_profile = BusinessProfile.objects.get(business=instance.business)
        except BusinessProfile.DoesNotExist:
            return
            
        call = Call.objects.create(
            business=instance.business,
            caller_number=payload.get('caller_number', ''),
            started_at=timezone.now(),
            transcript=transcript
        )
        
        try:
            res = engine.analyse_call(transcript, business_profile.business_name, business_profile.get_business_type_display(), instance=instance)
            call.outcome = res.get("outcome", "unknown")
            call.save(update_fields=["outcome"])
        except PermissionRequired as pr:
            if "res" in locals():
                call.outcome = res.get("outcome", "unknown")
                call.save(update_fields=["outcome"])
                
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
