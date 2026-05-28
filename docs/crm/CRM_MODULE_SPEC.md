# BengalBound HUB — CRM & Lead Management System Spec
# BengalBound Ltd | "Light. Easy. Powerful."

> **Document Class:** Module Specification Document  
> **Target Audience:** Frontend Engineers, Backend Engineers, and AI Integration Teams  
> **Date:** May 2026 | **Version:** 1.0  

---

## 1. Overview
The CRM module (`modules.crm`) and Leads module (`modules.leads`) serve as the business development foundation inside the BengalBound HUB. It provides custom deals pipelines, contacts directories, and is designed to sync seamlessly with Salesforce, HubSpot, and Pipedrive through the **Crux (AI CRM Manager)** and **Lead Hunter (AI B2B SDR)** agents.

---

## 2. Core Entities & Data Architecture

```
  BusinessInstance (bredbound.BusinessInstance)
         │
         ├── Contact (modules.crm.models.Contact)
         │     ├── Full Name, Email, Phone, Company Name
         │     └── Intent Score (AI 0-100)
         │
         └── Deal (modules.crm.models.Deal)
               ├── Title, Value, Stage, Pipeline
               └── Status (open, won, lost, cold)
```

### Models Specs
1.  **Contact (`modules.crm.models.Contact`)**:
    *   Links to `BusinessInstance` to enforce multi-tenancy.
    *   Tracks Apollo.io enrichment fields (technographics, company size, funding).
2.  **Deal (`modules.crm.models.Deal`)**:
    *   Maps to a custom sales pipeline stage.
    *   Audited dynamically by the CS agent (Mira) to flag "deals going cold".

---

## 3. External Integrations
*   **HubSpot Sync:** Real-time Webhooks to synchronize contact registrations and timeline events.
*   **Gmail & SMTP Routing:** Direct outbox parsing allowing AI agents to draft and send sales sequences.
