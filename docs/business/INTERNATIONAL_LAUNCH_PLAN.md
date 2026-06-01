# International Launch Plan
# BengalBound HUB — BengalBound Ltd
**Version:** 1.0 | **Date:** June 2026 | **Owner:** CEO + Head of Growth

---

## 1. Launch Philosophy

BengalBound is built for the world but launching from Bangladesh. Our strategy is **community-led, market-by-market** — not a simultaneous global launch. Each market gets a tailored entry with localized pricing, language, and compliance.

---

## 2. Market Priority & Timeline

### Phase 1 — Home Market (Month 1–3)
**Bangladesh**
- Platform language: English + Bengali
- Currency: BDT (৳)
- Payment: bKash, Nagad, Rocket, Visa/Mastercard via SSLCommerz
- Compliance: Bangladesh Cybersecurity Act, Data Protection Act
- Channels: Facebook groups, LinkedIn, Dhaka startup community, BASIS, BASIS SoftExpo
- Target verticals: garment exporters, retail chains, clinics, schools, restaurants
- CAC target: $5–15

### Phase 2 — UK + EU Diaspora (Month 3–6)
**United Kingdom / Europe**
- Currency: GBP (£) / EUR (€)
- Payment: Stripe
- Compliance: GDPR (full), UK GDPR, EU AI Act
- Channels: UK Bengali business associations, LinkedIn UK, ProductHunt
- DPO requirement: appoint a Data Protection Officer or representative
- Target verticals: UK restaurants, beauty salons, accounting firms, letting agencies
- CAC target: $25–50

### Phase 3 — South East Asia (Month 6–12)
**Singapore, Malaysia, Indonesia**
- Currencies: SGD, MYR, IDR (localized)
- Payment: Stripe
- Compliance: PDPA (Singapore), PDPA (Thailand), OJK regulations (Indonesia)
- Channels: e27, Tech in Asia, local startup directories, Google Ads
- Target verticals: F&B, logistics SMEs, digital agencies
- CAC target: $20–40

### Phase 4 — Middle East (Month 9–15)
**UAE, Saudi Arabia, Qatar**
- Currencies: AED, SAR, QAR
- Payment: Stripe (Middle East supported)
- Compliance: UAE PDPL, Saudi PDPL — data residency may require GCC hosting
- Channels: Step Conference Dubai, LinkedIn MENA, Arabic content marketing
- Target verticals: hospitality, real estate, trading companies
- CAC target: $30–60

### Phase 5 — North America (Month 12–24)
**USA, Canada**
- Currency: USD
- Payment: Stripe
- Compliance: CCPA (California), PIPEDA (Canada), SOC 2 (for enterprise)
- Channels: ProductHunt, AppSumo, Hacker News, LinkedIn
- Target verticals: agencies, e-commerce brands, small professional services
- CAC target: $50–100

---

## 3. Localization Requirements

### Currently implemented in codebase
- Multi-currency pricing: USD, EUR, GBP, BDT, INR (session-based)
- Currency symbol auto-display on pricing page
- `set_currency` view at `/set-currency/?currency=GBP`

### Still needed for full i18n
- [ ] Bengali language translations (Django `gettext`, `.po` files)
- [ ] Arabic RTL support (CSS `dir="rtl"`)
- [ ] Currency exchange rate API (replace static `EXCHANGE_RATES` dict with live rates)
- [ ] Time zone per business (`BusinessInstance.timezone` field)
- [ ] Local date/number formatting

---

## 4. Payment Gateway by Region

| Region | Gateway | Notes |
|---|---|---|
| Bangladesh | SSLCommerz + bKash | Most BD businesses use mobile money |
| Global | Stripe | 135+ currencies, handles tax |
| Middle East | Stripe MENA | Available in UAE, SA, QA |
| India | Razorpay | Better than Stripe for INR |
| SE Asia | Stripe / 2Checkout | Depends on country |

**Implementation:** See `docs/platform/PAYMENT_INTEGRATION.md`

---

## 5. Compliance by Region

| Region | Key Regulation | Our Status |
|---|---|---|
| EU/UK | GDPR + EU AI Act | Architecture compliant, DPO needed |
| Bangladesh | Cybersecurity Act + DPA | Compliant |
| Singapore | PDPA | Compliant |
| USA | CCPA | Data deletion endpoint needed |
| UAE | PDPL | Data residency review needed |
| India | DPDP Act | Consent mechanism needed |

**Full compliance details:** See `docs/legal/INTERNATIONAL_COMPLIANCE.md`

---

## 6. Go-To-Market by Channel

### Content Marketing (Organic — Month 1 onwards)
- Blog posts at `/blog/` targeting SME pain points by country
- YouTube demos of each AI agent
- LinkedIn thought leadership (CEO + team)
- SEO: target "AI employee for [industry]" + "business management software [country]"

### Community / Product-Led Growth
- Product Hunt launch (target #1 of the day)
- AppSumo Lifetime Deal (Year 1 growth hack — 500–2000 LTD buyers)
- Hacker News "Show HN" post
- Reddit: r/entrepreneur, r/SaaS, r/smallbusiness

### Partnerships
- Accounting software integrations (QuickBooks, Tally, Xero)
- Domain registrars (bundled offer)
- Bangladesh chamber of commerce partnerships
- UK Bengali Business Association sponsorship

### Paid Acquisition (Month 6+ when profitable)
- Google Ads: target "[competitor] alternative" keywords
- LinkedIn Ads for B2B decision-makers
- Facebook/Instagram for SME owners (BD + UK)

---

## 7. Launch Day Checklist

- [ ] Domain live and pointing to Netlify (public site) + Render (app)
- [ ] Stripe keys set, test payment working end-to-end
- [ ] Email working (Brevo/Mailgun SMTP configured)
- [ ] SSL certificates active (Cloudflare handles this)
- [ ] Trial signup flow tested
- [ ] Seed data loaded (`seed_modules` + `seed_agents`)
- [ ] At least 3 real testimonials / case studies on homepage
- [ ] Privacy policy + Terms of Service pages live
- [ ] Cookie consent banner live (GDPR)
- [ ] Google Analytics / Plausible tracking live
- [ ] StatusPage set up (e.g. Betteruptime free tier)
- [ ] Support email configured
- [ ] ProductHunt draft ready

---

## 8. KPIs to Track

| Metric | Month 1 Target | Month 6 Target |
|---|---|---|
| Signups | 50 | 500 |
| Paying clients | 10 | 100 |
| MRR | $500 | $8,000 |
| CAC | < $30 | < $25 |
| Churn | < 10% | < 5% |
| NPS | > 30 | > 50 |
