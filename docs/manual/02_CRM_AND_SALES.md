# CRM & Sales — Module Manual

**Modules covered:** CRM · Leads · Invoicing · Contracts · Deal Flow · Commission · B2B Portal · Omnichannel

---

## CRM (`/hub/<slug>/crm/`)

Central contact and pipeline management.

### Contacts
- Store people and companies with email, phone, address, job title, industry, tags
- Full interaction history (calls, emails, meetings, notes) per contact
- Owner assignment for team accountability

### Pipelines & Deals
- Create multiple pipelines (e.g. "New Business", "Upsell")
- Each pipeline has stages with a win probability % and colour
- Deals track: value, currency, expected close date, priority, owner
- Move deals across stages by drag-and-drop or edit form
- Mark deals as Won or Lost with a reason

### Activities
Log calls, emails, meetings, and tasks against any contact or deal. Visible in a chronological timeline.

**AI Integration:** Hire **Crux** to auto-score contacts, run follow-up sequences, and receive weekly pipeline reports.

---

## Leads (`/hub/<slug>/leads/`)

Capture and qualify inbound leads before converting them to CRM contacts.

### Lead Lifecycle
`new` → `contacted` → `qualified` → `proposal` → `negotiation` → `won` / `lost`

### Key Fields
- Source (web form, referral, cold outreach, etc.)
- Priority and estimated value
- Assigned team member
- Lead activities: calls, emails, meetings

### Converting a Lead
When qualified, convert a Lead to a CRM Contact + Deal. Conversion date is logged.

**AI Integration:** Hire **Lead Hunter** to research new prospects automatically via web search and score them against your ICP.

---

## Invoicing (`/hub/<slug>/invoicing/`)

Create, send, and track professional invoices.

### Invoice Flow
`draft` → `sent` → `viewed` → `partial` → `paid` → `overdue` / `cancelled`

### Features
- Multi-currency support
- Tax lines per invoice line
- Partial payments — track amount paid vs outstanding
- PDF generation and email delivery

### Payments
Record payments manually (cash, bank transfer, card, cheque, online) with reference and notes.

---

## Contracts (`/hub/<slug>/contracts/`)

Draft, send, and e-sign contracts.

### Contract Templates
Save reusable contract templates with variable placeholders (e.g. `{{client_name}}`, `{{start_date}}`).

### Contract Flow
`draft` → `sent` → `viewed` → `signed` → `expired` / `cancelled`

### Signing
Each party (sender/signer/CC) gets an email. Signature data, IP address, and timestamp are recorded on signing.

**AI Integration:** Hire **Sage** for AI contract review — flags risky clauses before you send.

---

## Deal Flow (`/hub/<slug>/deals/` — Real Estate)

Deal pipeline from first enquiry to completion.

- Track deal type: purchase, sale, lease, referral, dual
- Milestones with due dates and completion tracking
- Attach documents (ID, financial, contracts, inspection reports) per deal
- Notes and approval trail

---

## Commission (`/hub/<slug>/commission/`)

Sales commission tracking and payout.

- Define commission rules per agent: agent split %, broker split %, referral fee %
- Log each deal with gross commission income
- Track paid/unpaid status and payment date
- Annual cap enforcement

---

## B2B Portal (`/b2b/` — suite prefix)

Self-service portal for your wholesale or trade customers.

- Customer tiers: standard / silver / gold / platinum — each with its own pricing
- Credit limits and outstanding balance tracking
- Customers browse and place orders directly
- Order statuses: draft → submitted → confirmed → processing → shipped → delivered

---

## Omnichannel (`/omnichannel/` — suite prefix)

Unified sales channel management.

- Connect sales channels: POS, website, Shopify, WooCommerce, Amazon, eBay, TikTok, Instagram, B2B portal
- Manage channel listings: listed price, stock qty, sync status
- Sync logs show last sync status and record count per channel
