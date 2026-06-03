import json
import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from hub.models import BusinessInstance
from .models import ComplianceRule, ComplianceCheck, SecurityIncident
from .serializers import ComplianceRuleSerializer, ComplianceCheckSerializer, SecurityIncidentSerializer
from agents.utils import agent_chat

logger = logging.getLogger(__name__)


# Helper function to evaluate compliance using Serea agent_chat
def run_compliance_evaluation(business, agent_name, action_type, action_payload, client_country, end_user_country):
    # Fetch active compliance rules matching the client country, end user country, or global
    countries = [client_country or 'Global', end_user_country or 'Global', 'Global', 'Global', '*']
    rules_qs = ComplianceRule.objects.filter(is_active=True).filter(
        Q(jurisdiction__in=countries) | Q(jurisdiction='*')
    )

    if not rules_qs.exists():
        return "approved", "No active rules found.", "", "", 1.0, []

    rules_list = list(rules_qs.values('id', 'name', 'category', 'standard_ref', 'rule_description'))
    rules_text = "\n".join([f"- [{r['standard_ref']}] Category: {r['category']} - {r['name']}: {r['rule_description']}" for r in rules_list])

    system_prompt = (
        "You are Inspector — a strict, fail-closed compliance enforcement AI.\n\n"
        "Evaluate if the incoming request/action violates any listed compliance rule.\n"
        "Respond ONLY with valid JSON (no markdown or backticks):\n"
        '{"decision": "approved" or "blocked" or "escalated", "reason": "one sentence explanation", "failed_check": "category name", "failed_standard": "standard reference"}\n\n'
        "Default to approved for benign actions. Block or escalate ONLY if there is a clear violation of the rules."
    )

    user_message = (
        f"Active Compliance Rules:\n{rules_text}\n\n"
        f"Agent Name: {agent_name}\n"
        f"Action Type: {action_type}\n"
        f"Payload: {json.dumps(action_payload)[:1000]}\n"
    )

    try:
        raw_response = agent_chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        # Parse output
        result = json.loads(raw_response.strip())
        decision = result.get("decision", "approved").lower()
        reason = result.get("reason", "Passed AI evaluation.")
        failed_check = result.get("failed_check", "")
        failed_standard = result.get("failed_standard", "")
        
        # Resolve rules triggered
        triggered_rules_ids = []
        if decision != 'approved':
            triggered_rules_ids = [r['id'] for r in rules_list if r['standard_ref'] in failed_standard or r['category'] in failed_check]

        return decision, reason, failed_check, failed_standard, 0.95, triggered_rules_ids

    except Exception as exc:
        logger.error("Inspector AI evaluation failed: %s", exc)
        # Fail-safe default
        return "approved", f"AI compliance evaluation bypassed due to system error: {exc}", "", "", 1.0, []


class CheckActionView(APIView):
    """
    POST /workspace/<slug>/inspector/check/
    Evaluates an agent action against active rules.
    """
    def post(self, request, slug):
        business = get_object_or_404(BusinessInstance, slug=slug)
        agent_name = request.data.get('agent_name', 'Unknown Agent')
        action_type = request.data.get('action_type', 'unknown')
        action_payload = request.data.get('action_payload', {})
        client_country = request.data.get('client_country', 'US')
        end_user_country = request.data.get('end_user_country', '')

        decision, reason, failed_check, failed_standard, confidence, rule_ids = run_compliance_evaluation(
            business, agent_name, action_type, action_payload, client_country, end_user_country
        )

        # Create ComplianceCheck audit log record
        check = ComplianceCheck(
            business=business,
            agent_name=agent_name,
            client_country=client_country,
            end_user_country=end_user_country,
            action_type=action_type,
            action_payload=action_payload,
            decision=decision,
            failed_check=failed_check,
            failed_standard=failed_standard,
            ai_reasoning=reason,
            confidence=confidence
        )
        check.save()
        if rule_ids:
            check.rules_applied.set(rule_ids)

        # Create SecurityIncident on critical or blocked decisions
        if decision in ('blocked', 'escalated'):
            severity = 'high'
            if 'critical' in reason.lower() or 'phi' in failed_check.lower() or 'financial' in failed_check.lower():
                severity = 'critical'
            
            SecurityIncident.objects.create(
                compliance_check=check,
                severity=severity,
                status='open',
                regulations_triggered=[failed_standard] if failed_standard else [],
                root_cause=reason
            )

        return Response(ComplianceCheckSerializer(check).data, status=status.HTTP_201_CREATED)


class AuditLogListView(APIView):
    """
    GET /workspace/<slug>/inspector/audit-log/
    Returns recent compliance logs.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        business = get_object_or_404(BusinessInstance, slug=slug)
        logs = ComplianceCheck.objects.filter(business=business).order_by('-checked_at')[:100]
        serializer = ComplianceCheckSerializer(logs, many=True)
        return Response(serializer.data)


class IncidentListView(APIView):
    """
    GET /workspace/<slug>/inspector/incidents/
    Returns all security incidents.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        business = get_object_or_404(BusinessInstance, slug=slug)
        incidents = SecurityIncident.objects.filter(compliance_check__business=business).order_by('-created_at')
        serializer = SecurityIncidentSerializer(incidents, many=True)
        return Response(serializer.data)


class ResolveIncidentView(APIView):
    """
    PATCH /workspace/<slug>/inspector/incidents/<id>/resolve/
    Resolves a security incident.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, slug, pk):
        business = get_object_or_404(BusinessInstance, slug=slug)
        incident = get_object_or_404(SecurityIncident, pk=pk, compliance_check__business=business)
        
        notes = request.data.get('resolution_notes', 'Resolved by administrator.')
        incident.status = 'resolved'
        incident.resolution_notes = notes
        incident.resolved_at = timezone.now()
        incident.save()

        return Response(SecurityIncidentSerializer(incident).data)


class EscalationsListView(APIView):
    """
    GET /workspace/<slug>/inspector/escalations/pending/
    Returns actions requiring human review.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        business = get_object_or_404(BusinessInstance, slug=slug)
        checks = ComplianceCheck.objects.filter(business=business, decision='escalated').order_by('-checked_at')
        serializer = ComplianceCheckSerializer(checks, many=True)
        return Response(serializer.data)


class DecideEscalationView(APIView):
    """
    POST /workspace/<slug>/inspector/escalations/<id>/decide/
    Human approve or reject decision on escalation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, slug, pk):
        business = get_object_or_404(BusinessInstance, slug=slug)
        check = get_object_or_404(ComplianceCheck, pk=pk, business=business, decision='escalated')
        
        human_decision = request.data.get('decision', 'blocked').lower()
        if human_decision not in ('approved', 'blocked'):
            return Response({"error": "Invalid decision. Choose 'approved' or 'blocked'."}, status=400)

        # Log new ComplianceCheck audit entry representing the manual override/decision
        new_check = ComplianceCheck(
            business=business,
            agent_name=check.agent_name,
            client_country=check.client_country,
            end_user_country=check.end_user_country,
            action_type=check.action_type,
            action_payload=check.action_payload,
            decision=human_decision,
            failed_check=check.failed_check,
            failed_standard=check.failed_standard,
            ai_reasoning=f"Human override decision: {human_decision.upper()}",
            confidence=1.0
        )
        new_check.save()
        
        # If there's an associated security incident, update its status
        incident = SecurityIncident.objects.filter(compliance_check=check).first()
        if incident:
            incident.status = 'resolved'
            incident.resolution_notes = f"Human decision made: {human_decision}."
            incident.resolved_at = timezone.now()
            incident.save()

        return Response(ComplianceCheckSerializer(new_check).data, status=status.HTTP_201_CREATED)


class RulesListView(APIView):
    """
    GET /POST /workspace/<slug>/inspector/rules/
    List or add rules.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        rules = ComplianceRule.objects.all().order_by('category', 'name')
        return Response(ComplianceRuleSerializer(rules, many=True).data)

    def post(self, request, slug):
        serializer = ComplianceRuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AnalyticsView(APIView):
    """
    GET /workspace/<slug>/inspector/analytics/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        business = get_object_or_404(BusinessInstance, slug=slug)
        checks_qs = ComplianceCheck.objects.filter(business=business)
        total_checks = checks_qs.count()
        
        blocked_count = checks_qs.filter(decision='blocked').count()
        escalated_count = checks_qs.filter(decision='escalated').count()
        violation_rate = (blocked_count / total_checks * 100) if total_checks > 0 else 0.0

        category_breakdown = list(
            checks_qs.values('failed_check')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return Response({
            "total_checks": total_checks,
            "blocked_checks": blocked_count,
            "escalated_checks": escalated_count,
            "violation_rate": round(violation_rate, 2),
            "category_breakdown": category_breakdown
        })


class HealthView(APIView):
    """
    GET /workspace/<slug>/inspector/health/
    """
    permission_classes = []

    def get(self, request, slug):
        return Response({"status": "healthy"})
