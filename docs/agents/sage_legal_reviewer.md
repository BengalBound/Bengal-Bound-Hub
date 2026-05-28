# Module Requirements: Sage — AI Legal Document Reviewer
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `sage` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 DocuSign API, Google Drive API, PDF/DOCX processing

---

## Section 1: Overview

**AI Employee Name:** Sage | **Department:** Legal & Compliance
**Target Clients:** SMEs, agencies, startups, HR departments, procurement teams — any business that regularly deals with contracts, NDAs, or compliance documents but can't afford a full-time lawyer.
**Core Function:** Reviews contracts, NDAs, and compliance documents in minutes — flags risky clauses, summarizes obligations, compares against standard templates, and generates a plain-English risk report.
**Value Prop:** *"Know exactly what you're signing before you sign it. No lawyer on retainer."*

| | Human Lawyer (Contract Review) | Sage AI |
|---|---|---|
| Monthly Retainer | ৳60,000–৳1,00,000 | ৳2,000 |
| Review Time/Contract | 2–5 days | 2–5 minutes |
| Plain-English Summary | Rarely provided | Always included |
| Clause Risk Flagging | Manual, billed by hour | Automated + scored |

---

## Section 2: Core Capabilities

1. **Contract Upload & Parse** — Upload PDF or DOCX; Sage extracts all clauses and sections with structure preserved
2. **Risk Scoring** — Each clause scored for risk level (0–100); overall contract risk score on the cover page
3. **Plain-English Summary** — Every clause explained in simple language: what it means, what you're agreeing to
4. **Red Flag Detection** — Automatically flags: unfair termination clauses, unlimited liability, non-compete overreach, IP assignment traps, payment term risks
5. **Clause Comparison** — Compare against client's standard templates; highlights deviations requiring negotiation
6. **Obligation Tracker** — Extracts all obligations, deadlines, and responsibilities into a checklist
7. **NDA Classifier** — Specialized NDA analysis: scope, duration, jurisdiction, confidentiality exceptions
8. **Negotiation Suggestions** — Gemini suggests alternative clause wording for flagged risks

---

## Section 3: Django Models

```python
class DocumentTemplate(models.Model):
    """Client's standard contract templates for comparison"""
    TYPES = [('nda','NDA'),('service_agreement','Service Agreement'),
             ('employment','Employment Contract'),('msa','MSA'),
             ('vendor','Vendor Agreement'),('partnership','Partnership')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='sage_documenttemplates')
    name            = models.CharField(max_length=300)
    document_type   = models.CharField(max_length=30, choices=TYPES)
    file            = models.FileField(upload_to='legal/templates/')
    parsed_clauses  = models.JSONField(default=dict)
    uploaded_at     = models.DateTimeField(auto_now_add=True)

class LegalDocument(models.Model):
    STATUS = [('queued','Queued'),('reviewing','Reviewing'),('completed','Completed'),('failed','Failed')]
    TYPES = [('nda','NDA'),('contract','Contract'),('employment','Employment'),
             ('vendor','Vendor Agreement'),('compliance','Compliance Doc'),('other','Other')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='sage_legaldocuments')
    name            = models.CharField(max_length(500))
    document_type   = models.CharField(max_length(20), choices=TYPES)
    file            = models.FileField(upload_to='legal/documents/')
    compared_to     = models.ForeignKey(DocumentTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    overall_risk    = models.IntegerField(null=True)         # 0–100
    risk_label      = models.CharField(max_length(10), blank=True)  # 'low','medium','high','critical'
    executive_summary = models.TextField(blank=True)         # Gemini plain-English summary
    status          = models.CharField(max_length(20), choices=STATUS, default='queued')
    uploaded_at     = models.DateTimeField(auto_now_add=True)
    reviewed_at     = models.DateTimeField(null=True)

class Clause(models.Model):
    RISK = [('safe','Safe'),('caution','Caution'),('risky','Risky'),('critical','Critical')]
    document        = models.ForeignKey(LegalDocument, on_delete=models.CASCADE)
    clause_number   = models.CharField(max_length(50))
    clause_title    = models.CharField(max_length(500))
    original_text   = models.TextField()
    plain_english   = models.TextField()                     # Gemini explanation
    risk_level      = models.CharField(max_length(10), choices=RISK)
    risk_score      = models.IntegerField()                  # 0–100
    risk_reason     = models.TextField(blank=True)
    negotiation_suggestion = models.TextField(blank=True)    # Gemini alternative wording
    is_flagged      = models.BooleanField(default=False)
    template_deviation = models.TextField(blank=True)        # Deviation from client template

class Obligation(models.Model):
    document        = models.ForeignKey(LegalDocument, on_delete=models.CASCADE)
    description     = models.TextField()
    responsible_party = models.CharField(max_length(200))    # 'You', 'Counter-party', 'Both'
    deadline        = models.DateField(null=True, blank=True)
    is_completed    = models.BooleanField(default=False)
    clause_ref      = models.CharField(max_length(50))
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/sage/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/templates/` | Manage standard contract templates |
| `POST` | `/documents/upload/` | Upload document for review |
| `GET` | `/documents/` | List all reviewed documents |
| `GET` | `/documents/{id}/` | Full review: summary + clauses + risk |
| `GET` | `/documents/{id}/clauses/` | All clauses with risk scores |
| `GET` | `/documents/{id}/clauses/flagged/` | Only red-flagged clauses |
| `GET` | `/documents/{id}/obligations/` | Obligation checklist |
| `GET` | `/documents/{id}/report/` | Download PDF risk report |
| `POST` | `/documents/{id}/compare/` | Compare against a template |
| `GET` | `/analytics/` | Docs reviewed, avg risk score, flag frequency |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| PDF Parsing | `pdfplumber` | ✅ FREE |
| DOCX Parsing | `python-docx` | ✅ FREE |
| PDF Report | `reportlab` | ✅ FREE |
| DocuSign | DocuSign eSignature API | 💲 $25/mo |
| Task Queue | `django-apscheduler` | ✅ FREE |
| Storage | Google Cloud Storage (or local) | ✅ FREE tier |

```
pip install pdfplumber python-docx reportlab django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Document upload, clause extraction, risk scoring, plain-English summary, PDF report | Weeks 1–6 |
| Phase 2 | Template comparison, obligation tracker, NDA classifier, negotiation suggestions | Weeks 7–12 |
| Phase 3 | DocuSign integration, Google Drive sync, compliance checklist, multi-jurisdiction support | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Docs/mo | Features |
|---|---|---|---|
| Intern | Free | 2 | Risk score + plain-English summary |
| Entry | ৳2,000 | 10 | Full clause review, PDF report |
| Mid | ৳5,000 | 30 | Template comparison, obligation tracker |
| Senior | ৳10,000 | Unlimited | NDA classifier, negotiation suggestions, DocuSign |

---
*BengalBound HUB — dev branch*
