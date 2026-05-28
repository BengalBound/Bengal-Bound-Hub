# Module Requirements: Veritas — AI Client Onboarding & KYB Verification
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `veritas` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Company registry APIs, document verification APIs, FATF watchlists, Google Maps
> 🔒 **INTERNAL GATE MODULE — Every new client must pass before any AI agent is activated**

---

## Section 1: Overview & Mandate

**Module Name:** Veritas — Client Onboarding & Know Your Business (KYB) Verification
**AI Employee Name:** Veritas *(Latin: Truth)*
**Department:** Internal Risk & Compliance (NeurolinkIT)

**Core Function:** Before any client can hire a Bengal Bound AI employee, Veritas verifies they are a **legally registered, legitimate business entity** operating in accordance with applicable law. No AI agent is activated for any client until Veritas issues a **Green KYB Clearance**.

> ### 🛡️ The Veritas Mandate
> *"We only work with real businesses. Every client is verified against company registries, sanctions lists, and AML watchlists before a single AI agent is activated. No exceptions."*

---

## Section 2: KYB Verification Process

### 2.1 Onboarding Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     VERITAS ONBOARDING FLOW                        │
│                                                                     │
│  Client Signs Up ──► Veritas Activation                            │
│                              │                                      │
│  ┌───────────────────────────▼──────────────────────────────────┐  │
│  │  STEP 1: Business Registration Details Collected             │  │
│  │  Company legal name, registration number, jurisdiction,      │  │
│  │  registered address, incorporation date, business type       │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────▼──────────────────────────────────┐  │
│  │  STEP 2: Document Upload                                     │  │
│  │  Certificate of Incorporation / Trade License                │  │
│  │  VAT / Tax Registration Certificate                          │  │
│  │  Proof of Business Address (utility bill / bank statement)   │  │
│  │  Government-issued ID of company director/owner             │  │
│  │  (Passport / National ID / Driver's License)                 │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────▼──────────────────────────────────┐  │
│  │  STEP 3: Automated Verification (Gemini + Registry APIs)    │  │
│  │  ✅ Company registry check (RJSC BD / Companies House UK /   │  │
│  │     MCA India / ASIC AU / SEC US / ACRA SG / others)        │  │
│  │  ✅ Document authenticity check (AI + optical verification)  │  │
│  │  ✅ Director ID document verification                        │  │
│  │  ✅ Sanctions screening (OFAC / UN / EU / UK / FATF)        │  │
│  │  ✅ AML / PEP watchlist check                                │  │
│  │  ✅ Adverse media scan (legal cases, fraud allegations)      │  │
│  │  ✅ Business address geolocation validation                  │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────▼──────────────────────────────────┐  │
│  │  STEP 4: Risk Scoring                                        │  │
│  │  Green (0–30): Auto-approved → AI agents activated          │  │
│  │  Amber (31–60): Human review required within 48 hours       │  │
│  │  Red (61–100): Rejected + client notified with reason       │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────▼──────────────────────────────────┐  │
│  │  STEP 5: Agreement Signing                                   │  │
│  │  Digital signature on:                                      │  │
│  │  • Platform Terms of Service                                │  │
│  │  • Data Processing Agreement (DPA — GDPR compliant)        │  │
│  │  • Acceptable Use Policy (no illegal activities)           │  │
│  │  • AI Ethics Acknowledgement                                │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                              │ ALL PASSED                          │
│              ┌───────────────▼────────────────┐                   │
│              │  ✅ GREEN KYB CLEARANCE ISSUED  │                   │
│              │  AI Agents Now Available        │                   │
│              └────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 2.2 Company Registry APIs by Country

| Country / Region | Registry | API / Source |
|---|---|---|
| **Bangladesh** | RJSC (Registrar of Joint Stock Companies) | RJSC portal lookup + OCR verification |
| **United States** | SEC EDGAR + State-level SOS databases | SEC EDGAR API, OpenCorporates |
| **United Kingdom** | Companies House | Companies House REST API (free) |
| **European Union** | National registries (Handelsregister DE, KVK NL, etc.) | OpenCorporates + EU Business Registers API |
| **India** | MCA (Ministry of Corporate Affairs) | MCA21 API + CIN verification |
| **Singapore** | ACRA (Accounting & Corporate Regulatory Authority) | ACRA BizFile+ API |
| **Australia** | ASIC + ABN Lookup | ABN Lookup API (free), ASIC Connect |
| **Canada** | Corporations Canada | Industry Canada API |
| **UAE** | DED (Dept of Economic Development) | DED smart lookup |
| **Saudi Arabia** | MISA + Ministry of Commerce | MCI company lookup |
| **South Africa** | CIPC (Companies and Intellectual Property Commission) | CIPC e-services |
| **Nigeria** | CAC (Corporate Affairs Commission) | CAC verification portal |
| **Malaysia** | SSM (Suruhanjaya Syarikat Malaysia) | MySSM API |
| **Global fallback** | OpenCorporates | OpenCorporates API (150+ jurisdictions) |

---

### 2.3 Sanctions & AML Screening

Screened against:

| List | Issuer | Coverage |
|---|---|---|
| **OFAC SDN List** | US Treasury | US sanctions — individuals, entities, countries |
| **UN Consolidated Sanctions List** | United Nations | Global sanctions across all member states |
| **EU Consolidated Sanctions List** | European Union | EU-sanctioned individuals and entities |
| **UK HM Treasury Sanctions List** | UK Government | Post-Brexit UK sanctions |
| **FATF Black & Grey Lists** | Financial Action Task Force | High-risk and monitored jurisdictions |
| **World Bank Debarment List** | World Bank | Debarred from World Bank-funded projects |
| **Interpol Notices** | Interpol | Wanted individuals (Director check) |
| **PEP (Politically Exposed Persons)** | Multiple sources | Political figures who pose heightened risk |
| **Adverse Media** | Gemini-powered news scan | Fraud, corruption, money laundering allegations in last 5 years |

---

### 2.4 Document Verification

| Document | Verification Method |
|---|---|
| Certificate of Incorporation | OCR extraction + cross-check with company registry |
| Trade License | OCR + issuing authority verification |
| VAT / Tax Certificate | Tax authority lookup where API available |
| Proof of Address | Address extracted, validated via Google Maps API |
| Director's Passport | MRZ line check, expiry, issuing country format |
| Director's National ID | Format validation by country, cross-check with name |
| Bank Statement Header | Bank name, address, account name must match company |

---

### 2.5 Ongoing Monitoring (Post-Onboarding)

Veritas doesn't just verify once — it monitors continuously:
- **Quarterly re-verification** — re-run sanctions and registry checks every 90 days
- **License expiry alerts** — alert client 30 days before trade license/registration expires
- **Adverse media monitoring** — Gemini scans news for client company name weekly
- **Sanctions list updates** — real-time when OFAC/UN/EU lists update
- **Suspicious usage pattern detection** — Inspector flags + Veritas reviews if client's AI usage pattern changes dramatically (e.g., sudden spike in bulk email targeting known spam regions)

---

## Section 3: Risk Scoring Model

| Factor | Weight | Risk-Increasing Signals |
|---|---|---|
| Company registration age | 15% | Less than 6 months old |
| Jurisdiction risk | 20% | FATF grey/black listed country |
| Director ID match | 15% | Name mismatch, expired ID |
| Sanctions hit | 30% | Any hit = automatic Red |
| Adverse media | 10% | Fraud/corruption articles in last 5 years |
| Business type | 10% | High-risk industries (gambling, crypto, adult, firearms) |

**Risk Thresholds:**
- 🟢 **0–30 (Green)** → Auto-approved, AI agents activated immediately
- 🟡 **31–60 (Amber)** → Manual review by NeurolinkIT compliance team, decision within 48 hours
- 🔴 **61–100 (Red)** → Automatic rejection, client notified with compliant rejection reason

---

## Section 4: Required Client Agreements

Every client must digitally sign all four documents before activation:

### 4.1 Platform Terms of Service
- Permitted and prohibited uses of all AI agents
- No use for illegal activities, harassment, fraud, or deception
- Client is responsible for their own compliance with local laws
- NeurolinkIT reserves the right to terminate for ToS violations

### 4.2 Data Processing Agreement (DPA)
- GDPR Article 28 compliant
- Defines NeurolinkIT as Data Processor, client as Data Controller
- Sub-processor list (Google Cloud, Gemini)
- Data retention, deletion, and breach notification obligations
- EU Standard Contractual Clauses (SCCs) included for EU clients

### 4.3 Acceptable Use Policy (AUP)
- Prohibited: illegal content, discriminatory targeting, spam, phishing, IP theft, competitor sabotage
- AI agents must not be directed to deceive end-users about being AI (Aria must always disclose)
- Client may not attempt to bypass Inspector compliance checks
- Violation = immediate termination + potential legal referral

### 4.4 AI Ethics Acknowledgement
- Client acknowledges AI agents are not infallible and require human oversight
- Client accepts responsibility for reviewing and approving AI outputs before material actions
- Client agrees not to use AI agents to cause harm to individuals or communities

---

## Section 5: Django Models

```python
class ClientApplication(models.Model):
    STATUS = [
        ('submitted','Submitted'),('documents_pending','Documents Pending'),
        ('under_review','Under Review — Automated'),('human_review','Human Review'),
        ('approved','Approved'),('rejected','Rejected'),('suspended','Suspended')
    ]
    RISK_LEVEL = [('green','Green'),('amber','Amber'),('red','Red')]

    user                = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company_legal_name  = models.CharField(max_length=500)
    registration_number = models.CharField(max_length=200)
    jurisdiction        = models.CharField(max_length=100)   # Country/state
    registered_address  = models.TextField()
    incorporation_date  = models.DateField(null=True)
    business_type       = models.CharField(max_length=200)   # 'Agency', 'Clinic', etc.
    website             = models.URLField(blank=True)
    vat_number          = models.CharField(max_length=100, blank=True)
    director_name       = models.CharField(max_length=300)
    director_email      = models.EmailField()
    director_phone      = models.CharField(max_length=30)

    # Verification results
    registry_verified   = models.BooleanField(null=True)
    sanctions_clear     = models.BooleanField(null=True)
    aml_clear           = models.BooleanField(null=True)
    documents_verified  = models.BooleanField(null=True)
    risk_score          = models.IntegerField(null=True)         # 0–100
    risk_level          = models.CharField(max_length=10, choices=RISK_LEVEL, blank=True)
    gemini_risk_summary = models.TextField(blank=True)

    # Status
    status              = models.CharField(max_length=30, choices=STATUS, default='submitted')
    rejection_reason    = models.TextField(blank=True)
    reviewed_by         = models.CharField(max_length=200, blank=True)
    approved_at         = models.DateTimeField(null=True)
    rejected_at         = models.DateTimeField(null=True)
    submitted_at        = models.DateTimeField(auto_now_add=True)
    next_review_date    = models.DateField(null=True)           # Quarterly re-check

class KYBDocument(models.Model):
    DOC_TYPES = [
        ('incorporation','Certificate of Incorporation'),
        ('trade_license','Trade License'),
        ('vat_cert','VAT/Tax Certificate'),
        ('proof_address','Proof of Business Address'),
        ('director_passport','Director Passport'),
        ('director_id','Director National ID'),
        ('bank_statement','Bank Statement Header'),
    ]
    STATUS = [('pending','Pending'),('verified','Verified'),('rejected','Rejected')]

    application         = models.ForeignKey(ClientApplication, on_delete=models.CASCADE)
    document_type       = models.CharField(max_length=30, choices=DOC_TYPES)
    file                = models.FileField(upload_to='kyb/documents/')
    ocr_extracted_data  = models.JSONField(default=dict)    # AI-extracted fields
    ai_verification     = models.BooleanField(null=True)
    rejection_reason    = models.TextField(blank=True)
    status              = models.CharField(max_length=20, choices=STATUS, default='pending')
    uploaded_at         = models.DateTimeField(auto_now_add=True)
    verified_at         = models.DateTimeField(null=True)

class SanctionsCheck(models.Model):
    application         = models.ForeignKey(ClientApplication, on_delete=models.CASCADE)
    checked_entity      = models.CharField(max_length=500)  # Company or director name
    list_checked        = models.CharField(max_length=100)  # 'OFAC', 'UN', 'EU', etc.
    match_found         = models.BooleanField(default=False)
    match_score         = models.FloatField(null=True)      # Fuzzy match score
    match_detail        = models.TextField(blank=True)
    checked_at          = models.DateTimeField(auto_now_add=True)

class ClientAgreement(models.Model):
    DOC_TYPES = [('tos','Terms of Service'),('dpa','Data Processing Agreement'),
                 ('aup','Acceptable Use Policy'),('ai_ethics','AI Ethics Acknowledgement')]
    application         = models.ForeignKey(ClientApplication, on_delete=models.CASCADE)
    agreement_type      = models.CharField(max_length=20, choices=DOC_TYPES)
    version             = models.CharField(max_length=20)   # e.g. 'v2.1'
    signed              = models.BooleanField(default=False)
    signed_at           = models.DateTimeField(null=True)
    ip_address          = models.GenericIPAddressField(null=True)
    signature_hash      = models.CharField(max_length=64)   # SHA-256 of signed content + timestamp
```

---

## Section 6: API Endpoints (`/hub/<slug>/api/agents/veritas/`)

| Method | Endpoint | Audience | Action |
|---|---|---|---|
| `POST` | `/apply/` | New client | Submit company details |
| `POST` | `/apply/{id}/documents/` | New client | Upload KYB documents |
| `GET` | `/apply/{id}/status/` | New client | Check application status |
| `POST` | `/apply/{id}/sign/{doc_type}/` | New client | Digitally sign agreement |
| `GET` | `/applications/` | NeurolinkIT ops | List all applications |
| `GET` | `/applications/{id}/` | NeurolinkIT ops | Full KYB detail |
| `PATCH` | `/applications/{id}/approve/` | NeurolinkIT ops | Manual approval |
| `PATCH` | `/applications/{id}/reject/` | NeurolinkIT ops | Manual rejection with reason |
| `POST` | `/applications/{id}/rescan/` | NeurolinkIT ops | Re-run sanctions/registry checks |
| `GET` | `/sanctions-checks/` | NeurolinkIT ops | Sanctions screening log |
| `GET` | `/analytics/` | NeurolinkIT ops | Approval rate, avg review time, risk distribution |

---

## Section 7: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash (document OCR + risk analysis) | ✅ FREE |
| Company Registry | OpenCorporates API | 💲 $99/mo (150+ jurisdictions) |
| Sanctions Screening | OpenSanctions.org API (open source data) | ✅ FREE (or $299/mo pro) |
| Document OCR | Google Cloud Vision API | 💲 $1.50/1K pages |
| Address Verification | Google Maps Geocoding API | 💲 $5/1K requests |
| E-Signature | Internal SHA-256 (or DocuSign for enterprise) | ✅ FREE / 💲 $25/mo |
| PDF Generation | `reportlab` (DPA / agreement PDFs) | ✅ FREE |
| Task Queue | `django-apscheduler` (quarterly re-checks) | ✅ FREE |

```
pip install google-cloud-vision googlemaps requests reportlab django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 8: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Application form, document upload, Gemini OCR, manual NeurolinkIT review, agreement signing | Weeks 1–4 |
| Phase 2 | OpenSanctions integration, OpenCorporates registry check, risk scoring, auto-approve/reject | Weeks 5–8 |
| Phase 3 | Quarterly re-monitoring, adverse media scan, licence expiry alerts, full analytics dashboard | Weeks 9–14 |

---

> **⚠️ Platform Gate:**
> The `ClientApplication.status` field is checked by Inspector before any AI agent API call. If status is not `approved`, all agent endpoints return `HTTP 403 — KYB Verification Required`. No workaround exists.

---
*BengalBound HUB — dev branch*
