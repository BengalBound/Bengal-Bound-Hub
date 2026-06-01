# BengalBound HUB — Legal & Compliance Standards
# BengalBound Ltd | "Light. Easy. Powerful."

> **Document Class:** Corporate Governance & Compliance Policy  
> **Target Audience:** CTO, DPO (Data Protection Officer), Legal Counsel, Compliance Engineers  
> **Date:** June 2026 | **Version:** 1.0  

---

## 1. Regulatory Context

BengalBound HUB operates inside a multi-national regulatory environment. Since our platform processes user communications, employee data, and financial transactions, we strictly enforce local and international privacy and AI alignment frameworks.

### Audited Regulations (40+ Global Frameworks)
1.  **GDPR (EU General Data Protection Regulation):**
    *   Right to erasure (Data deletion from all backups).
    *   Explicit consent logs for all tracking (Traffic logs consent banners).
2.  **EU AI Act:**
    *   Risk classification for autonomous AI employee agents.
    *   Strict logging and human overrides for high-risk operations.
3.  **PDPA (Singapore Personal Data Protection Act):**
    *   Prevention of unauthorized transfer of personal identifiers across borders.
4.  **Bangladesh Cybersecurity Act (BCA) & Data Protection Act (DPA):**
    *   Local hosting capabilities (hybrid cloud VPS / self-hosted installation options).
    *   Encryption at rest for confidential business databases.

---

## 2. Platform Compliance Controls

*   **Allowed IP Locklist (`BusinessAccessMiddleware`):** Restricts access to corporate dashboards to authorized IP brackets to prevent credentials exploitation.
*   **Encrypted Secrets Store:** Client API keys (Zendesk, Twilio, HubSpot) are Fernet-encrypted utilizing a secure project key stored exclusively in the OS environment.
*   **Immutable History Audit:** Built-in `HistoricalRecords` tracking ensures that any modifications made to user permissions or directories are permanently logged.
