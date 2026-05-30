# Payment Integration Guide
# BengalBound HUB — BengalBound Ltd
**Version:** 1.0 | **Date:** May 2026 | **Owner:** CTO + Finance

---

## Overview

BengalBound supports multi-currency pricing for a global SME audience. The platform displays localized prices automatically using session-based currency detection, and processes payments through Stripe (global) and SSLCommerz (Bangladesh).

---

## 1. Current Pricing Implementation

### Multi-Currency Display (Live in Codebase)

The `public_site/views.py` exchange rate system:

```python
EXCHANGE_RATES = {
    'USD': 1.0, 'EUR': 0.92, 'GBP': 0.79,
    'BDT': 110.0, 'INR': 83.0
}
CURRENCY_SYMBOLS = {
    'USD': '$', 'EUR': '€', 'GBP': '£', 'BDT': '৳', 'INR': '₹'
}
```

Users switch currency at `/set-currency/?currency=GBP`. Prices auto-convert.

### AI Employee Tier Prices (AIEmployeeTier model)
Stored as `monthly_price_usd` in the database. Converted to local currency at display time.

---

## 2. Stripe (Global Payments)

### Setup Steps
1. Create account at **stripe.com**
2. Complete business verification (takes 1–3 days)
3. Get API keys from Dashboard → Developers → API Keys

### Environment Variables
```bash
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Supported Currencies (135+)
Stripe handles USD, EUR, GBP, SGD, AED, SAR, CAD, AUD, and most global currencies natively.

### Integration Points Needed
- [ ] Subscription checkout: `/console/subscribe/<plan_id>/`
- [ ] Webhook handler: `/stripe/webhook/` (listens for `invoice.paid`, `customer.subscription.deleted`)
- [ ] Customer portal: `/console/billing/` (Stripe Customer Portal)
- [ ] Trial → paid conversion flow

### Stripe Connect (for marketplace model)
If BengalBound takes a platform cut from white-label partners:
- Use Stripe Connect (Express accounts)
- Platform fee: 10–20% of each transaction
- Automatic payouts to partner businesses

---

## 3. SSLCommerz (Bangladesh)

The primary payment gateway for Bangladesh customers (supports bKash, Nagad, Rocket, Visa, Mastercard).

### Setup Steps
1. Register at **sslcommerz.com** (requires trade licence + bank account)
2. Get sandbox credentials for testing
3. Install: `pip install sslcommerz-python`

### Environment Variables
```bash
SSLCOMMERZ_STORE_ID=your_store_id
SSLCOMMERZ_STORE_PASS=your_store_password
SSLCOMMERZ_SANDBOX=False  # True for testing
```

### Payment Methods Available
- bKash (most popular — 70M+ users)
- Nagad, Rocket, Upay (mobile banking)
- Visa, Mastercard, AMEX (cards)
- Internet banking (DBBL, BRAC, Dutch-Bangla, etc.)

---

## 4. Razorpay (India)

For INR customers. Better conversion rates than Stripe in India.

```bash
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...
```

Supports UPI, NEFT, cards, net banking.

---

## 5. Pricing Tiers — Recommended Global Rates

| Plan | USD | EUR | GBP | BDT | SGD |
|---|---|---|---|---|---|
| Freemium | $0 | €0 | £0 | ৳0 | S$0 |
| Entry | $9 | €8 | £7 | ৳990 | S$12 |
| Standard | $29 | €27 | £23 | ৳2,990 | S$39 |
| Premium | $79 | €73 | £63 | ৳7,990 | S$105 |
| Advance | $199 | €183 | £157 | ৳19,900 | S$269 |

### AI Agent Add-on Pricing
| Tier | USD/mo | BDT/mo |
|---|---|---|
| Intern (entry agent) | Free | Free |
| Entry level | $9 | ৳990 |
| Mid level | $19 | ৳2,000 |
| Senior level | $49 | ৳5,000 |

---

## 6. Tax Handling

| Region | Tax | Approach |
|---|---|---|
| EU | VAT (20–27%) | Stripe Tax (auto-calculates) |
| UK | VAT 20% | Stripe Tax |
| Bangladesh | VAT 15% + IT Withholding | Manual invoice |
| USA | Sales tax (varies by state) | Stripe Tax |
| UAE | VAT 5% | Stripe Tax |

Enable **Stripe Tax** in dashboard to auto-handle EU/UK/US VAT.

---

## 7. Refund & Cancellation Policy

- Monthly subscriptions: cancel anytime, no refund for partial month
- Annual subscriptions: pro-rata refund within 30 days
- AI agent fees: refund within 7 days if agent fails to perform
- Bangladesh policy: 7-day cooling-off per Consumer Rights Protection Act

---

## 8. Revenue Recognition

- SaaS subscriptions: recognized monthly (MRR)
- Annual plans: deferred revenue, recognized monthly
- One-time setup fees: recognized at service delivery
- Affiliate commissions: 20–30% of referred MRR, paid monthly

---

## 9. Implementation Checklist

- [ ] Stripe account verified + live keys set in Render
- [ ] SSLCommerz account approved (for BD market)
- [ ] Subscription model wired to `AIEmployeeTier` + `HubPlanConfig`
- [ ] Webhook handlers created for payment events
- [ ] Stripe Tax enabled for EU/UK/US
- [ ] Billing portal page at `/console/billing/`
- [ ] Invoice PDF generation working
- [ ] Failed payment retry logic (Stripe handles automatically)
- [ ] Currency selector visible on pricing page
- [ ] Test end-to-end payment in sandbox
