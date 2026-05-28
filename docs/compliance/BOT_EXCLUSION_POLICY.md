# Bot Exclusion & Machine-Readable Rules Policy

**Purpose:** To define how BengalBound's autonomous AI agents interact with third-party technical boundaries.

## 1. Respecting robots.txt
BengalBound operates the `BengalBoundBot/1.0` web crawler. This crawler must **always** evaluate the `robots.txt` protocol at the root of a target domain before initiating any HTTP request. 

*   If `User-agent: BengalBoundBot` or `User-agent: *` is assigned `Disallow: /`, the scraper **must immediately terminate** the request.
*   The `urllib.robotparser` library must be strictly integrated into `agents/toolkit.py`. 
*   Ignoring `robots.txt` is considered a critical security violation.

## 2. Emerging Standards (llms.txt / ai.txt)
As the web adopts new standards like `llms.txt` and `ai.txt` to opt out of AI ingestion, BengalBound engineering commits to monitoring these standards. Future updates to the `check_robots_txt` function will include parsing for these explicit AI-exclusion files.

## 3. Rate Limiting (Politeness)
To avoid excessive server load (which could be legally interpreted as trespass to chattels or a DDoS attack):
*   BengalBoundBot will parse and obey the `Crawl-Delay` directive in `robots.txt`.
*   If `Crawl-Delay` is detected, the agent will sleep for the mandated number of seconds prior to extraction.
*   In the absence of a `Crawl-Delay`, a default 0s is assumed, but concurrent parallel scraping of a single domain is strictly prohibited.
