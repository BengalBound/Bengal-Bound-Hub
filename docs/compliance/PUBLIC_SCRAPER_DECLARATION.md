# Public Scraper Declaration

**URL:** `https://bengalbound.com/bot-policy`

BengalBound operates an autonomous fleet of AI agents designed to automate B2B tasks such as SEO auditing, competitor analysis, and market research. To fulfill these tasks, our agents occasionally need to read publicly available information from the internet.

## Identity Details
All requests made by our AI agents will clearly identify themselves using the following HTTP header:
`User-Agent: BengalBoundBot/1.0 (+https://bengalbound.com/bot-policy)`

## Our Commitment
*   **We only read public data:** Our bot does not bypass paywalls, CAPTCHAs, or authentication barriers.
*   **We do not harvest personal data:** We operate an aggressive PII-stripping pipeline that removes emails and phone numbers before data is stored or processed by our AI models.
*   **We do not scrape to train foundational models:** Data extracted by our agents is used strictly to fulfill immediate client requests (e.g., an SEO audit report), not to train massive LLMs.

## How to Opt-Out
If you are a webmaster and do not want BengalBoundBot to crawl your site, simply add the following to your `robots.txt` file at the root of your domain:

```text
User-agent: BengalBoundBot
Disallow: /
```

Our systems will automatically respect this instruction within 24 hours. If you experience any issues, please contact legal@bengalbound.com.
