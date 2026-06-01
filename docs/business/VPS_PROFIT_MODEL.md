# VPS Hosting + Ollama Profit Model
# BengalBound Ltd — Bengal Bound
**Owner:** CEO + CTO | **Updated:** June 2026

> This document answers: what does it cost to run Bengal Bound on a VPS with local AI (Ollama),
> what can we charge, and how much profit do we make at each growth stage?

---

## 1. Why VPS + Ollama Instead of Cloud AI APIs?

| Approach | Cost Model | Margin | Risk |
|---|---|---|---|
| LiteLLM proxy (LITELLM_BASE_URL) (pay-per-call) | ~$0.15 per 1M tokens | Low (API costs scale with usage) | API price changes |
| VPS + Ollama (self-hosted) | Fixed monthly server cost | Very high (90%+ gross margin) | Need to manage server |
| Hybrid (Ollama primary, LiteLLM proxy fallback) | Mostly fixed, small variable | High (95%+ typically) | Minimal |

**Decision: Hybrid approach.** Ollama on VPS handles 95% of calls. LiteLLM proxy (LITELLM_BASE_URL) handles overflow or premium requests.

---

## 2. VPS Server Options (Recommended: Hetzner)

Hetzner is used by major global SaaS companies. Bangladesh devs can manage it via SSH from anywhere.

| Stage | Server | Specs | Cost/mo | Ollama Models | Clients |
|---|---|---|---|---|---|
| **Startup** | Hetzner CX42 | 8 vCPU · 16GB RAM · 160GB SSD | ~$19 | Mistral 7B · Phi-3 Mini · Gemma 2B | 0–50 |
| **Growth** | Hetzner AX52 | 12 vCPU · 64GB RAM · 512GB NVMe | ~$56 | Llama 3 8B · Mistral 7B · Qwen 14B | 50–300 |
| **Scale** | Hetzner AX102 | 24 vCPU · 128GB RAM · 1TB NVMe | ~$146 | Llama 3 70B · Qwen 72B | 300–1,000 |
| **Enterprise** | Hetzner GPU (RTX 4000) | GPU · 64GB · 1TB | ~$380 | Any model, faster | 1,000+ |

**Alternative providers:** DigitalOcean, Vultr, OVHcloud. Hetzner offers the best price-to-performance ratio.

**Bangladesh-friendly note:** Hetzner payment accepts international debit/credit cards. Server is in Germany (low latency to EU/UK clients) or Finland. For BD clients, add a Cloudflare CDN layer.

### Recommended Ollama Models by Use Case

| Model | Size | Best For | RAM Needed |
|---|---|---|---|
| `mistral:7b` | 4.1GB | General chat, email triage, Concierge | 8GB |
| `llama3:8b` | 4.7GB | Content generation (Serea), reasoning | 8GB |
| `phi3:mini` | 2.3GB | Quick classification, Inspector | 4GB |
| `qwen2.5:14b` | 9GB | Complex tasks, better quality | 16GB |
| `llama3:70b` | 40GB | Premium tier, best quality | 48GB |

**Startup recommendation:** Run `mistral:7b` + `phi3:mini` on CX42. Total RAM use: ~10GB. Leaves room for Django + PostgreSQL.

---

## 3. Full Monthly Infrastructure Costs

### Stage 1: Startup (Months 1–6, 0–50 clients)

| Item | Cost/Month |
|---|---|
| Hetzner CX42 VPS (Django + Ollama + PostgreSQL) | $19 |
| Hetzner Volume 100GB (database backups) | $5 |
| django-allauth (built into Django) | $0 |
| Cloudflare (free tier — CDN + WAF) | $0 |
| Domain (bengalbound.io — annualised) | $1 |
| Google Workspace (2 users: CEO + CTO) | $12 |
| LiteLLM proxy (overflow — ~1M tokens/mo) | $1 |
| Uptime monitoring (UptimeRobot free) | $0 |
| GitHub (free tier) | $0 |
| **Total Monthly Cost** | **$38/month** |

### Stage 2: Growth (Months 7–18, 50–300 clients)

| Item | Cost/Month |
|---|---|
| Hetzner AX52 VPS | $56 |
| Hetzner Volume 500GB | $23 |
| Hetzner Load Balancer | $6 |
| django-allauth (included in Django) | $0 |
| Cloudflare Pro | $20 |
| Google Workspace (10 users) | $60 |
| LiteLLM proxy (overflow — ~10M tokens/mo) | $8 |
| Sentry error monitoring | $26 |
| **Total Monthly Cost** | **~$199/month** |

### Stage 3: Scale (Months 18+, 300–1,000 clients)

| Item | Cost/Month |
|---|---|
| Hetzner AX102 VPS (×2 for redundancy) | $292 |
| Managed PostgreSQL (Hetzner) | $40 |
| django-allauth (included) | $0 |
| Cloudflare Business | $200 |
| Google Workspace (25 users) | $150 |
| LiteLLM proxy (premium overflow) | $30 |
| Sentry + monitoring stack | $80 |
| **Total Monthly Cost** | **~$792/month** |

---

## 4. Pricing Tiers (Monthly Subscription per Agent)

### Bangladesh Market (BDT Pricing)

| Plan | Price/Agent/Month | Who It's For |
|---|---|---|
| NGO / Startup | ৳1,500 (~$14) | Registered NGOs, early-stage startups |
| Starter | ৳2,500 (~$23) | Small businesses, freelancers |
| Growth | ৳4,000 (~$36) | SMEs with 2–10 agents |
| Pro | ৳6,000 (~$55) | Agencies, established businesses |

### International Market (USD Pricing)

| Plan | Price/Agent/Month | Includes |
|---|---|---|
| Starter | $29 | 1 agent, basic support, mock AI |
| Pro | $49 | Up to 5 agents, real AI (Ollama), compliance dashboard |
| Business | $79 | Up to 15 agents, priority support, custom system prompts |
| Enterprise | $149+ | Unlimited agents, SLA, dedicated onboarding |

### AppSumo Lifetime Deal (One-Time, Launch Campaign)

| Tier | Price | What They Get | Break-Even for Us |
|---|---|---|---|
| Tier 1 | $69 | 3 agents forever | 3 months of $29 service |
| Tier 2 | $139 | 8 agents forever | 3 months of $49 service |
| Tier 3 | $209 | Unlimited agents for 1 site | 4 months of $49 service |

**AppSumo revenue share:** AppSumo takes 30%. Our net: $48, $97, $146 per sale.
**Target:** 500 sales in launch week → ~$50,000 upfront cash → fund hiring + marketing.

---

## 5. Profit Calculations — The Real Numbers

### Assumptions
- Average client has 3 agents subscribed
- Average price per agent: $35 (blended BD + international)
- Infrastructure scales with clients (see Stage costs above)

### MRR and Profit by Client Count

| Clients | Agents (avg 3) | Avg Price | MRR | Infra Cost | **Gross Profit** | **Margin** |
|---|---|---|---|---|---|---|
| 5 | 15 | $35 | $525 | $38 | **$487** | **93%** |
| 15 | 45 | $35 | $1,575 | $38 | **$1,537** | **98%** |
| 30 | 90 | $38 | $3,420 | $56 | **$3,364** | **98%** |
| 50 | 150 | $40 | $6,000 | $100 | **$5,900** | **98%** |
| 100 | 300 | $42 | $12,600 | $199 | **$12,401** | **98%** |
| 200 | 600 | $45 | $27,000 | $350 | **$26,650** | **99%** |
| 500 | 1,500 | $45 | $67,500 | $792 | **$66,708** | **99%** |
| 1,000 | 3,000 | $49 | $147,000 | $1,500 | **$145,500** | **99%** |

> **Why the margin is so high:** Ollama on VPS costs are fixed regardless of how many AI calls you make. The more clients you add, the higher the margin gets (infrastructure doesn't scale linearly). This is the fundamental advantage of self-hosted AI over API-based AI.

### Break-Even Analysis

| Expense Category | Monthly Cost | Break-Even (# clients needed) |
|---|---|---|
| VPS infrastructure only | $38 | 2 clients |
| Infrastructure + CEO salary (৳80,000 = $730) | $768 | 22 clients |
| Infrastructure + full team (4 people) | $3,200 | 91 clients |
| Infrastructure + office + team | $5,000 | 143 clients |

---

## 6. Revenue Streams (All Sources)

| Stream | How | Realistic Year 1 Target |
|---|---|---|
| **Monthly SaaS subscriptions** | Auto-billed via Stripe | $18,000/yr (50 clients) |
| **AppSumo launch** | One-time lifetime deals | $50,000 (500 sales) |
| **Fiverr/Upwork setup fees** | $99–499 per client setup | $10,000/yr (50 setups) |
| **B2B direct contracts** | Custom enterprise deals | $20,000/yr (2–3 deals) |
| **NGO grants** | USAID, Gates, Google.org | $10,000–50,000 (grant-dependent) |
| **Government BD grants** | ICT Division, BASIS venture | $5,000–15,000 |
| **White-label resellers** | Agencies re-sell Bengal Bound | $5,000/yr (Phase 2) |
| **Total Year 1 (realistic)** | | **$68,000–$118,000** |

---

## 7. NGO / Social Enterprise Strategy

**Why this matters:**
- Bangladesh has 500,000+ registered NGOs that cannot afford human staffing
- AI agents at ৳1,500/mo ($14) are accessible even to small NGOs
- NGO use = case studies, press coverage, grant eligibility, mission credibility

**How to execute:**
1. Register Bengal Bound as a **Social Enterprise** with RJSC (allows for-profit + social mission)
2. Offer **NGO Free Tier**: 1 agent free (Concierge or Serea) for registered Bangladeshi NGOs
3. Require case study / testimonial in exchange
4. Use NGO testimonials to apply for:
   - **USAID Digital Development grants** (up to $25K)
   - **Google.org Impact Challenge** (up to $1M)
   - **ICT Division's "Digital Bangladesh" tech grants**
   - **BASIS Social Innovation Fund**
5. Publish NGO impact report quarterly: "X NGOs served, X hours saved, X jobs created"

**Example NGO pitch:**
> "Bengal Bound gives your NGO an AI Concierge, an AI Content Strategist, and an AI Compliance Officer for less than ৳1,500/month — so your human team can focus on impact, not admin."

---

## 8. Competitive Positioning on Price

| Platform | Price | Our Equivalent | Saving |
|---|---|---|---|
| Hiring a part-time assistant in BD | ৳15,000/mo ($136) | ৳2,500/mo ($23) | **83% cheaper** |
| Hiring a full-time content writer in BD | ৳40,000/mo ($364) | ৳4,000/mo ($36) | **90% cheaper** |
| Jasper AI (content) | $49/mo | $36/mo + 4 other agents | **More value** |
| Zapier (automation) | $29/mo | $29/mo + AI reasoning | **More value** |
| Salesforce Einstein | $500/mo | $79/mo (Business plan) | **84% cheaper** |
| Hiring 3 staff in USA | $15,000/mo | $147/mo (Business plan) | **99% cheaper** |

---

*BengalBound Ltd — VPS Profit Model v1.0 | Update quarterly as pricing evolves.*
