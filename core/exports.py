"""
core/exports.py
──────────────
Standardised CSV export interface for all BengalBound modules.

Usage (function-based):
    from core.exports import csv_response
    return csv_response('production_orders', headers, rows)

Usage (mixin for class-based views):
    class MyExport(CsvExportMixin, View):
        filename = 'contacts'
        headers = ['Name', 'Email', 'Phone']

        def get_rows(self):
            return [[c.full_name, c.email, c.phone]
                    for c in Contact.objects.filter(business=self.biz)]
"""
import csv
from datetime import date
from django.http import HttpResponse


def csv_response(filename: str, headers: list, rows) -> HttpResponse:
    """
    Build and return a streaming CSV HttpResponse.

    Args:
        filename: base name without extension (date is appended automatically)
        headers:  list of column header strings
        rows:     iterable of iterables (one per row)
    """
    today = date.today().isoformat()
    safe_name = filename.replace(' ', '_').lower()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{safe_name}_{today}.csv"'

    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response


class CsvExportMixin:
    """
    Mixin for function-based or class-based views.
    Subclass and define `filename`, `headers`, and `get_rows()`.

    For FBV convenience, call `self.as_csv_response()` or use `csv_export_view`.
    """
    filename: str = 'export'
    headers: list = []

    def get_rows(self):
        raise NotImplementedError("Subclasses must implement get_rows()")

    def as_csv_response(self) -> HttpResponse:
        return csv_response(self.filename, self.headers, self.get_rows())


def make_export_view(filename: str, headers: list, queryset_fn, row_fn):
    """
    Factory: returns a plain Django view function for a CSV download.

    Args:
        filename:     base name for the downloaded file
        headers:      column header list
        queryset_fn:  callable(request, slug) → queryset
        row_fn:       callable(obj) → list of values
    """
    from django.contrib.auth.decorators import login_required

    @login_required
    def export_view(request, slug):
        qs = queryset_fn(request, slug)
        rows = (row_fn(obj) for obj in qs)
        return csv_response(filename, headers, rows)

    return export_view


# ── Pre-built export helpers for common modules ───────────────────────────────

def crm_contacts_csv(contacts) -> HttpResponse:
    headers = ['Name', 'Type', 'Email', 'Phone', 'Company', 'City', 'Country', 'Tags', 'Created']
    rows = [
        [
            c.full_name, c.contact_type, c.email, c.phone,
            c.company_name, c.city, c.country, c.tags,
            c.created_at.strftime('%Y-%m-%d'),
        ]
        for c in contacts
    ]
    return csv_response('crm_contacts', headers, rows)


def crm_deals_csv(deals) -> HttpResponse:
    headers = ['Title', 'Value', 'Currency', 'Stage', 'Pipeline', 'Contact',
               'Probability %', 'Expected Close', 'Status']
    rows = [
        [
            d.title,
            float(d.value) if d.value else 0,
            d.currency,
            d.stage.name if d.stage else '',
            d.stage.pipeline.name if d.stage and d.stage.pipeline else '',
            d.contact.full_name if d.contact else '',
            d.probability,
            d.expected_close.strftime('%Y-%m-%d') if d.expected_close else '',
            d.status,
        ]
        for d in deals
    ]
    return csv_response('crm_deals', headers, rows)


def invoicing_csv(invoices) -> HttpResponse:
    headers = ['Invoice #', 'Client', 'Amount', 'Currency', 'Status', 'Due Date', 'Issued']
    rows = []
    for inv in invoices:
        rows.append([
            getattr(inv, 'invoice_number', inv.pk),
            getattr(inv, 'client_name', ''),
            getattr(inv, 'total_amount', 0),
            getattr(inv, 'currency', 'USD'),
            getattr(inv, 'status', ''),
            getattr(inv, 'due_date', ''),
            inv.created_at.strftime('%Y-%m-%d') if hasattr(inv, 'created_at') else '',
        ])
    return csv_response('invoices', headers, rows)


def hr_employees_csv(employees) -> HttpResponse:
    headers = ['Name', 'Employee ID', 'Email', 'Phone', 'Department', 'Role', 'Active', 'Joined']
    rows = [
        [
            e.name, e.employee_id, e.email, e.phone,
            e.department, e.get_role_display(),
            'Yes' if e.is_active else 'No',
            e.joined_at.strftime('%Y-%m-%d') if hasattr(e, 'joined_at') else '',
        ]
        for e in employees
    ]
    return csv_response('employees', headers, rows)


def serea_moderation_csv(logs) -> HttpResponse:
    headers = ['Date', 'Platform', 'Comment (truncated)', 'Action', 'Sentiment',
               'Confidence', 'Requires Human']
    rows = [
        [
            log.created_at.strftime('%Y-%m-%d %H:%M'),
            log.platform,
            (log.comment_text or '')[:120],
            log.action_taken,
            log.sentiment_score or '',
            log.confidence_score or '',
            'Yes' if log.requires_human else 'No',
        ]
        for log in logs
    ]
    return csv_response('serea_moderation_logs', headers, rows)
