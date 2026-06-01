"""
LangChain tools that give agents read/write access to hub module data.
Each factory is scoped to a single BusinessInstance so queries never
cross business boundaries.

Agent-to-tool mapping (P2):
  crux, lead-hunter  → CRM tools
  hera, nexus        → HR tools
  cash               → Invoice tools
  reporting-bot      → all of the above
  (all others)       → universal toolkit only
"""
import json
import logging
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# CRM — Crux, Lead Hunter
# ─────────────────────────────────────────────────────────────────────────────

def make_crm_tools(business) -> list:

    def get_contacts(query: str = "") -> str:
        """List CRM contacts. Pass query to filter by name, email, or company."""
        try:
            from django.db.models import Q
            from modules.crm.models import Contact
            qs = Contact.objects.filter(business=business).order_by("-created_at")
            if query:
                qs = qs.filter(
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(email__icontains=query) |
                    Q(company_name__icontains=query)
                )
            data = [
                {
                    "name": c.full_name,
                    "email": c.email,
                    "company": c.company_name,
                    "phone": c.phone,
                    "tags": c.tags,
                }
                for c in qs[:30]
            ]
            return json.dumps(data, indent=2) if data else "No contacts found."
        except Exception as exc:
            return f"Error: {exc}"

    def get_deals(stage_filter: str = "") -> str:
        """List open (not won/lost) CRM deals. Optionally filter by stage name."""
        try:
            from modules.crm.models import Deal
            qs = (
                Deal.objects
                .filter(business=business, is_won=False, is_lost=False)
                .select_related("stage", "contact")
                .order_by("-amount")
            )
            if stage_filter:
                qs = qs.filter(stage__name__icontains=stage_filter)
            data = [
                {
                    "name": d.name,
                    "amount": float(d.amount),
                    "currency": d.currency,
                    "stage": d.stage.name if d.stage else None,
                    "contact": d.contact.full_name if d.contact else None,
                    "priority": d.priority,
                    "expected_close": str(d.expected_close) if d.expected_close else None,
                }
                for d in qs[:30]
            ]
            return json.dumps(data, indent=2) if data else "No open deals found."
        except Exception as exc:
            return f"Error: {exc}"

    def get_pipeline_summary() -> str:
        """Get pipeline KPIs: open deal count, total value by stage, and won totals."""
        try:
            from django.db.models import Sum, Count
            from modules.crm.models import Deal
            open_qs = Deal.objects.filter(business=business, is_won=False, is_lost=False)
            by_stage = list(
                open_qs
                .values("stage__name")
                .annotate(count=Count("id"), total=Sum("amount"))
                .order_by("-total")
            )
            won = Deal.objects.filter(business=business, is_won=True).aggregate(
                count=Count("id"), total=Sum("amount")
            )
            return json.dumps(
                {
                    "open_pipeline": by_stage,
                    "open_deal_count": open_qs.count(),
                    "won": {"count": won["count"] or 0, "total": float(won["total"] or 0)},
                },
                indent=2,
                default=str,
            )
        except Exception as exc:
            return f"Error: {exc}"

    def create_contact(
        first_name: str,
        last_name: str = "",
        email: str = "",
        company: str = "",
        phone: str = "",
    ) -> str:
        """Create a new CRM contact and return its ID."""
        try:
            from modules.crm.models import Contact
            c = Contact.objects.create(
                business=business,
                first_name=first_name,
                last_name=last_name,
                email=email,
                company_name=company,
                phone=phone,
                contact_type="company" if company and not first_name else "person",
            )
            return f"Created contact: {c.full_name} (ID: {c.pk})"
        except Exception as exc:
            return f"Error: {exc}"

    def log_activity(
        deal_id: int,
        activity_type: str,
        title: str,
        notes: str = "",
    ) -> str:
        """Log an activity (call/email/meeting/task/note) against a CRM deal."""
        try:
            from modules.crm.models import Deal, Activity
            deal = Deal.objects.get(pk=deal_id, business=business)
            act = Activity.objects.create(
                business=business,
                deal=deal,
                activity_type=activity_type,
                title=title,
                notes=notes,
            )
            return f"Activity logged: {act.title} (ID: {act.pk}) on deal '{deal.name}'"
        except Exception as exc:
            return f"Error: {exc}"

    return [
        StructuredTool.from_function(
            get_contacts, name="crm_get_contacts",
            description="List CRM contacts, optionally filtered by name/email/company.",
        ),
        StructuredTool.from_function(
            get_deals, name="crm_get_deals",
            description="List open CRM deals, optionally filtered by stage name.",
        ),
        StructuredTool.from_function(
            get_pipeline_summary, name="crm_pipeline_summary",
            description="Get pipeline KPIs: deal counts, values by stage, and won totals.",
        ),
        StructuredTool.from_function(
            create_contact, name="crm_create_contact",
            description="Create a new CRM contact with name, email, company, and phone.",
        ),
        StructuredTool.from_function(
            log_activity, name="crm_log_activity",
            description="Log a call, email, meeting, task, or note against a CRM deal.",
        ),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# HR — Hera, Nexus
# ─────────────────────────────────────────────────────────────────────────────

def make_hr_tools(business) -> list:

    def get_employees(department: str = "", status: str = "active") -> str:
        """List employees. Filter by department name or status (active/inactive/on_leave/terminated)."""
        try:
            from modules.hr.models import Employee
            qs = Employee.objects.filter(business=business).select_related("department", "position")
            if status:
                qs = qs.filter(status=status)
            if department:
                qs = qs.filter(department__name__icontains=department)
            data = [
                {
                    "name": e.full_name,
                    "department": e.department.name if e.department else None,
                    "position": e.position.title if e.position else None,
                    "status": e.status,
                    "contract_type": e.contract_type,
                    "hire_date": str(e.hire_date),
                    "years_of_service": e.years_of_service,
                }
                for e in qs[:50]
            ]
            return json.dumps(data, indent=2) if data else "No employees found."
        except Exception as exc:
            return f"Error: {exc}"

    def get_pending_leaves() -> str:
        """Get all pending leave requests awaiting approval."""
        try:
            from modules.hr.models import LeaveRequest
            qs = (
                LeaveRequest.objects
                .filter(business=business, status="pending")
                .select_related("employee", "leave_type")
                .order_by("start_date")
            )
            data = [
                {
                    "id": lr.pk,
                    "employee": lr.employee.full_name,
                    "leave_type": lr.leave_type.name if lr.leave_type else None,
                    "start_date": str(lr.start_date),
                    "end_date": str(lr.end_date),
                    "days": lr.days,
                    "reason": lr.reason[:120],
                }
                for lr in qs
            ]
            return json.dumps(data, indent=2) if data else "No pending leave requests."
        except Exception as exc:
            return f"Error: {exc}"

    def get_headcount_by_department() -> str:
        """Get active employee headcount grouped by department."""
        try:
            from django.db.models import Count
            from modules.hr.models import Employee
            result = list(
                Employee.objects
                .filter(business=business, status="active")
                .values("department__name")
                .annotate(count=Count("id"))
                .order_by("-count")
            )
            total = sum(r["count"] for r in result)
            return json.dumps({"total_active": total, "by_department": result}, indent=2)
        except Exception as exc:
            return f"Error: {exc}"

    def get_performance_reviews(employee_name: str = "") -> str:
        """Get performance reviews, optionally filtered by employee name."""
        try:
            from modules.hr.models import PerformanceReview
            from django.db.models import Q
            qs = PerformanceReview.objects.filter(business=business).select_related("employee")
            if employee_name:
                qs = qs.filter(
                    Q(employee__first_name__icontains=employee_name) |
                    Q(employee__last_name__icontains=employee_name)
                )
            data = [
                {
                    "employee": r.employee.full_name,
                    "period": f"{r.period_start} to {r.period_end}",
                    "rating": r.get_rating_display() if r.rating else "Not rated",
                    "status": r.status,
                }
                for r in qs[:20]
            ]
            return json.dumps(data, indent=2) if data else "No reviews found."
        except Exception as exc:
            return f"Error: {exc}"

    return [
        StructuredTool.from_function(
            get_employees, name="hr_get_employees",
            description="List employees, optionally filtered by department or status.",
        ),
        StructuredTool.from_function(
            get_pending_leaves, name="hr_pending_leaves",
            description="Get all pending leave requests awaiting approval.",
        ),
        StructuredTool.from_function(
            get_headcount_by_department, name="hr_headcount",
            description="Get active employee headcount grouped by department.",
        ),
        StructuredTool.from_function(
            get_performance_reviews, name="hr_performance_reviews",
            description="Get performance reviews, optionally filtered by employee name.",
        ),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Invoicing / Finance — Cash
# ─────────────────────────────────────────────────────────────────────────────

def make_invoice_tools(business) -> list:

    def get_invoices(status: str = "") -> str:
        """List invoices. Status options: draft, sent, viewed, partial, paid, overdue, cancelled."""
        try:
            from modules.invoicing.models import Invoice
            qs = (
                Invoice.objects
                .filter(business=business)
                .select_related("client")
                .order_by("-issue_date")
            )
            if status:
                qs = qs.filter(status=status)
            data = [
                {
                    "number": inv.invoice_number,
                    "client": str(inv.client),
                    "total": float(inv.total),
                    "amount_paid": float(inv.amount_paid),
                    "balance_due": float(inv.balance_due),
                    "status": inv.status,
                    "issue_date": str(inv.issue_date),
                    "due_date": str(inv.due_date) if inv.due_date else None,
                    "overdue": inv.is_overdue,
                }
                for inv in qs[:30]
            ]
            return json.dumps(data, indent=2) if data else "No invoices found."
        except Exception as exc:
            return f"Error: {exc}"

    def get_revenue_summary() -> str:
        """Get total invoiced amount, amount collected, and outstanding balance."""
        try:
            from django.db.models import Sum, Count
            from modules.invoicing.models import Invoice
            agg = (
                Invoice.objects
                .filter(business=business)
                .exclude(status="cancelled")
                .aggregate(total=Sum("total"), paid=Sum("amount_paid"), count=Count("id"))
            )
            overdue_count = (
                Invoice.objects
                .filter(business=business)
                .exclude(status__in=("paid", "cancelled"))
                .count()
            )
            return json.dumps(
                {
                    "invoice_count": agg["count"] or 0,
                    "total_invoiced": float(agg["total"] or 0),
                    "total_collected": float(agg["paid"] or 0),
                    "outstanding": float((agg["total"] or 0) - (agg["paid"] or 0)),
                    "overdue_invoice_count": overdue_count,
                },
                indent=2,
            )
        except Exception as exc:
            return f"Error: {exc}"

    def get_client_balance(client_name: str) -> str:
        """Get the outstanding balance for a specific client by name."""
        try:
            from django.db.models import Sum
            from modules.invoicing.models import Invoice
            qs = Invoice.objects.filter(
                business=business,
                client__name__icontains=client_name,
            ).exclude(status="cancelled")
            agg = qs.aggregate(total=Sum("total"), paid=Sum("amount_paid"))
            outstanding = float((agg["total"] or 0) - (agg["paid"] or 0))
            return json.dumps(
                {
                    "client_search": client_name,
                    "invoice_count": qs.count(),
                    "total_invoiced": float(agg["total"] or 0),
                    "total_paid": float(agg["paid"] or 0),
                    "outstanding": outstanding,
                },
                indent=2,
            )
        except Exception as exc:
            return f"Error: {exc}"

    return [
        StructuredTool.from_function(
            get_invoices, name="invoice_list",
            description="List invoices optionally filtered by status (draft/sent/paid/overdue/etc).",
        ),
        StructuredTool.from_function(
            get_revenue_summary, name="invoice_revenue_summary",
            description="Get total invoiced, collected, and outstanding balance across all invoices.",
        ),
        StructuredTool.from_function(
            get_client_balance, name="invoice_client_balance",
            description="Get the outstanding invoice balance for a specific client by name.",
        ),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Master factory
# ─────────────────────────────────────────────────────────────────────────────

_SLUG_FACTORIES = {
    "crux":           [make_crm_tools],
    "lead-hunter":    [make_crm_tools],
    "hera":           [make_hr_tools],
    "nexus":          [make_hr_tools],
    "cash":           [make_invoice_tools],
    "reporting-bot":  [make_crm_tools, make_hr_tools, make_invoice_tools],
    "nova":           [make_crm_tools, make_hr_tools, make_invoice_tools],
    "clarity":        [make_crm_tools, make_hr_tools, make_invoice_tools],
}


def get_hub_tools(business, agent_slug: str = None) -> list:
    """Return hub data tools scoped to this business and agent slug."""
    factories = _SLUG_FACTORIES.get(agent_slug, [])
    tools: list = []
    for factory in factories:
        try:
            tools.extend(factory(business))
        except Exception as exc:
            logger.warning("hub_tools %s failed for %s: %s", factory.__name__, agent_slug, exc)
    return tools
