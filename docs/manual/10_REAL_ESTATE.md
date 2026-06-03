# Real Estate — Module Manual

**Modules covered:** Property Listings · Deal Flow · RE Marketing · RE Client Portal · Commission

---

## Property Listings (`/properties/` — suite prefix)

Property database and listing management.

### Properties
Full listing record:
- Type: house, apartment, condo, commercial, office, land, industrial
- Listing type: for sale, for rent, or both
- Bedrooms, bathrooms, area (sqft), lot size
- Price (sale) and/or rent per month
- MLS number, listing URL, virtual tour URL
- Status: `active` / `under contract` / `sold` / `rented` / `off market` / `withdrawn`
- Listed by and listing date

### Property Showings
Schedule viewings against listings:
- Prospect name, scheduled date/time
- Showing status: `scheduled` / `completed` / `cancelled` / `no show`
- Notes from showing

**AI Integration:** Hire **Realt** to auto-generate listing descriptions, match listings to buyer criteria, and research market valuations.

---

## Deal Flow (`/deals/` — suite prefix)

Real estate transaction pipeline.

### Deals
Track a transaction from first enquiry to completion:
- Deal types: purchase, sale, lease, referral, dual agency
- Stage (configurable pipeline)
- Client name, email, phone
- Listing price, offer price, commission %
- Expected and actual close dates

### Deal Documents
Required documents per transaction with upload and approval tracking:
- Document types: ID, financial statements, contract, disclosure, inspection report, mortgage approval
- Source: agent-uploaded or client-uploaded
- Status: `pending` → `uploaded` → `approved` / `rejected`

### Deal Milestones
Key transaction dates:
- Offer accepted, inspection, contract signed, mortgage approval, completion
- Due date, done flag, completed timestamp

### Deal Notes
Internal notes per deal — visible to the assigned team only.

---

## RE Marketing (`/re-marketing/` — suite prefix)

Property marketing and lead nurturing.

### Listing Flyers
Auto-generate property flyers:
- Templates: standard, luxury, minimal, open house, just sold
- Headline, tagline, price, bedroom/bathroom details
- Agent contact information

### Drip Campaigns
Automated email nurture sequences for leads:
- Target audiences: buyers, sellers, renters, investors, past clients
- Status: `draft` → `active` → `paused` → `ended`

### Drip Messages
Sequence steps with: subject, body, delay in days from enrollment, type (email or SMS).

### Social Posts
Generate social content for listings:
- Post types: just listed, just sold, open house, price drop, under contract, market update
- Platforms: Facebook, Instagram, LinkedIn, or all
- Schedule for future publishing

**AI Integration:** Hire **Luma** for brand consistency and press release drafting. Hire **Oracle** for SEO-optimised listing descriptions.

---

## RE Client Portal (`/re-portal/` — suite prefix)

Secure portal for clients to track their transaction.

### Client Access
Agent creates a portal access link per client per deal:
- Token-based, expiry date
- Welcome message personalised to the transaction

### Portal Documents
Documents shared with the client through the portal:
- Document types: ID, financial, contract, disclosure, inspection, mortgage, other
- Signed flag — track what the client has signed
- Uploaded by agent or client

---

## Commission (`/hub/<slug>/commission/`)

Real estate commission calculation and tracking.

See [Finance Manual](03_FINANCE.md) and [CRM & Sales Manual](02_CRM_AND_SALES.md#commission) for full module details.

- Commission rules per agent with agent/broker/referral splits
- Annual cap enforcement
- Log each deal's gross commission income and split amounts
- Track paid vs unpaid commission entries
