from django.utils import timezone
import dateutil.parser
from agents.medibook.engine import MediBookEngine, PermissionRequired
from agents.medibook.models import Appointment, Doctor
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for MediBook."""
    engine = MediBookEngine()

    if event_type == 'patient_booked':
        try:
            appt_date = dateutil.parser.isoparse(payload.get('scheduled_at'))
        except (ValueError, TypeError):
            appt_date = timezone.now()

        doctor, _ = Doctor.objects.get_or_create(
            business=instance.business,
            name=payload.get('doctor_name', 'Unknown'),
            defaults={'specialty': payload.get('specialty', 'General Practice')}
        )

        reason = payload.get('reason', 'General checkup')

        appt, _ = Appointment.objects.get_or_create(
            doctor=doctor,
            patient_name=payload.get('patient_name', 'Unknown Patient'),
            scheduled_at=appt_date,
            defaults={
                'reason': reason,
                'duration': payload.get('duration', 30),
                'status': 'booked'
            }
        )

        try:
            res = engine.triage_urgency(reason, doctor.specialty, instance=instance)
            if res.get('urgency_level') == 'emergency':
                pass # The engine will raise PermissionRequired if emergency
        except PermissionRequired as pr:
            AgentPermissionRequest.objects.create(
                instance=instance,
                context=pr.context,
                option_a=pr.option_a,
                option_b=pr.option_b,
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
