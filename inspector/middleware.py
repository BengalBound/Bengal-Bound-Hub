import json
import logging
from django.http import JsonResponse
from django.utils import timezone


logger = logging.getLogger(__name__)


class InspectorMiddleware:
    """
    Synchronous compliance monitor middleware.
    Intercepts mutating requests and runs compliance AI checks.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Bypass safe methods, admin panel, static, media, or inspector endpoints
        if request.method in ('GET', 'OPTIONS', 'HEAD') or request.path.startswith('/admin/') or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)

        if '/inspector/' in request.path:
            return self.get_response(request)

        # 2. Context resolution
        business = getattr(request, 'current_business', None)
        user = getattr(request, 'user', None)
        if user and not user.is_authenticated:
            user = None

        agent_name = "Web Client"
        action_type = f"{request.method} {request.path}"
        payload = self._get_request_body(request)

        client_country = 'US'
        end_user_country = ''

        # 3. Compliance AI Evaluation
        from inspector.views import run_compliance_evaluation
        from inspector.models import ComplianceCheck, SecurityIncident

        decision, reason, failed_check, failed_standard, confidence, rule_ids = run_compliance_evaluation(
            business, agent_name, action_type, payload, client_country, end_user_country
        )

        # 4. Write Audit Log
        check = ComplianceCheck(
            business=business,
            agent_name=agent_name,
            client_country=client_country,
            end_user_country=end_user_country,
            action_type=action_type,
            action_payload=payload,
            decision=decision,
            failed_check=failed_check,
            failed_standard=failed_standard,
            ai_reasoning=reason,
            confidence=confidence
        )
        check.save()
        if rule_ids:
            check.rules_applied.set(rule_ids)

        # 5. Block request if not approved
        if decision in ('blocked', 'escalated', 'auto_rejected'):
            severity = 'high'
            if 'critical' in reason.lower():
                severity = 'critical'
            
            SecurityIncident.objects.create(
                compliance_check=check,
                severity=severity,
                status='open',
                regulations_triggered=[failed_standard] if failed_standard else [],
                root_cause=reason
            )

            return JsonResponse({
                "error": "Blocked by Inspector",
                "message": reason
            }, status=403)

        return self.get_response(request)

    def _get_request_body(self, request):
        try:
            if request.content_type == 'application/json':
                return json.loads(request.body)
        except Exception:
            pass
        try:
            return dict(request.POST)
        except Exception:
            return {}
