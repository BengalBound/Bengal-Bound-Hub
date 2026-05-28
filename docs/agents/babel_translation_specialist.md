# Module Requirements: Babel — AI Translation Specialist
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `babel` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Google Cloud Translation API, DeepL API, WordPress REST API, file processing

---

## Section 1: Overview

**AI Employee Name:** Babel | **Department:** Localization
**Target Clients:** Businesses expanding internationally, e-commerce stores selling globally, app developers, legal firms needing document translation, and content agencies serving multilingual markets.
**Core Function:** Translates documents, website copy, support tickets, and marketing materials across 50+ languages with brand-voice consistency — enabling global expansion without hiring translators for each market.
**Value Prop:** *"Go global overnight. 50+ languages. Your brand voice. Zero translation agency fees."*

| | Human Translator | Babel AI |
|---|---|---|
| Monthly Cost | ৳20,000–৳40,000 | ৳2,000 |
| Languages | 1–2 | 50+ |
| Turnaround | Days per document | Minutes |
| Brand Consistency | Variable | Enforced via style guide |

---

## Section 2: Core Capabilities

1. **Document Translation** — PDF, DOCX, XLSX, TXT files translated end-to-end with formatting preserved
2. **Website Localization** — Connects to WordPress or via file upload; translates all pages while preserving HTML structure and SEO metadata
3. **Brand-Voice Translation** — Client uploads brand style guide; Babel maintains terminology, tone, and brand-specific vocabulary across all languages
4. **Real-Time Support Translation** — Translates inbound customer support tickets instantly; agents reply in English, customer receives reply in their language
5. **Marketing Copy Translation** — Ad copy, email campaigns, and social media captions translated with cultural nuance, not literal word-for-word
6. **Translation Memory** — Stores previously translated segments; reuses exact matches for consistency and speed
7. **Glossary Management** — Client defines product names, slogans, and terms that must never be translated

---

## Section 3: Django Models

```python
class LanguagePair(models.Model):
    source_language = models.CharField(max_length=10)   # ISO 639-1 code e.g. 'en'
    target_language = models.CharField(max_length(10))
    is_active       = models.BooleanField(default=True)

class BrandStyleGuide(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='babel_brandstyleguides')
    tone            = models.CharField(max_length(50))   # 'formal', 'casual', 'technical'
    industry        = models.CharField(max_length(100))
    avoid_terms     = models.JSONField(default=list)
    preferred_terms = models.JSONField(default=dict)     # {'localise': 'localize'} equivalents
    sample_text     = models.TextField(blank=True)

class Glossary(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='babel_glossaries')
    term            = models.CharField(max_length(300))  # Source term (never translate this)
    note            = models.CharField(max_length(300), blank=True)  # e.g., "Brand name"
    language_pair   = models.ForeignKey(LanguagePair, on_delete=models.SET_NULL, null=True, blank=True)

class TranslationJob(models.Model):
    TYPE = [('document','Document'),('website','Website'),('support','Support Ticket'),
            ('marketing','Marketing Copy'),('custom','Custom Text')]
    STATUS = [('queued','Queued'),('processing','Processing'),('completed','Completed'),('failed','Failed')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='babel_translationjobs')
    job_type        = models.CharField(max_length(20), choices=TYPE)
    source_language = models.CharField(max_length(10))
    target_languages = models.JSONField()               # ['fr', 'de', 'ar']
    source_file     = models.FileField(upload_to='translations/source/', null=True, blank=True)
    source_text     = models.TextField(blank=True)
    word_count      = models.IntegerField(default=0)
    status          = models.CharField(max_length(20), choices=STATUS, default='queued')
    engine_used     = models.CharField(max_length(50))  # 'gemini', 'deepl', 'google'
    created_at      = models.DateTimeField(auto_now_add=True)
    completed_at    = models.DateTimeField(null=True)

class TranslationOutput(models.Model):
    job             = models.ForeignKey(TranslationJob, on_delete=models.CASCADE)
    target_language = models.CharField(max_length(10))
    translated_text = models.TextField()
    output_file     = models.FileField(upload_to='translations/output/', null=True, blank=True)
    quality_score   = models.FloatField(null=True)      # Internal consistency score
    created_at      = models.DateTimeField(auto_now_add=True)

class TranslationMemory(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='babel_translationmemories')
    source_segment  = models.TextField()
    source_language = models.CharField(max_length(10))
    target_segment  = models.TextField()
    target_language = models.CharField(max_length(10))
    usage_count     = models.IntegerField(default=1)
    last_used       = models.DateTimeField(auto_now=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/babel/`)

| Method | Endpoint | Action |
|---|---|---|
| `POST` | `/translate/text/` | Translate plain text |
| `POST` | `/translate/document/` | Upload and translate document |
| `POST` | `/translate/support-ticket/` | Real-time support ticket translation |
| `GET` | `/jobs/` | List all translation jobs |
| `GET` | `/jobs/{id}/` | Job detail + download outputs |
| `GET/POST` | `/glossary/` | Manage translation glossary |
| `GET/POST` | `/style-guide/` | Manage brand style guide |
| `GET` | `/memory/` | Browse translation memory |
| `GET` | `/supported-languages/` | List all 50+ supported languages |
| `GET` | `/analytics/` | Words translated, languages, turnaround |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| Translation API | Google Cloud Translation API | 💲 $20/1M chars |
| Premium Translation | DeepL API | 💲 $25/mo |
| PDF Parsing | `pdfplumber` | ✅ FREE |
| DOCX Handling | `python-docx` | ✅ FREE |
| Task Queue | `django-apscheduler` | ✅ FREE |

```
pip install google-cloud-translate deepl pdfplumber python-docx django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Text + document translation, Gemini engine, glossary, brand style guide, dashboard | Weeks 1–6 |
| Phase 2 | Translation memory, real-time support ticket translation, multi-language output, DeepL fallback | Weeks 7–12 |
| Phase 3 | Website localization (WordPress), marketing copy mode, quality scoring, XLSX support | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Words/mo | Features |
|---|---|---|---|
| Intern | Free | 5,000 | Text translation, 5 languages |
| Entry | ৳2,000 | 50,000 | Document translation, glossary |
| Mid | ৳5,000 | 200,000 | Translation memory, support tickets, 30 languages |
| Senior | ৳10,000 | Unlimited | All languages, website localization, brand voice |

---
*BengalBound HUB — dev branch*
