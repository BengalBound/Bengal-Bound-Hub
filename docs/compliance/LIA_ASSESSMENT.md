# Legitimate Interest Assessment (LIA)

**Under GDPR Article 6(1)(f) and the UK Data Protection Act**

## 1. Purpose Test
**What is the legitimate interest?**
BengalBound provides AI-driven B2B automation tools. To perform tasks like market research, SEO analysis, and public sentiment tracking, our autonomous agents must access public internet data. This processing helps our clients grow their businesses efficiently.

**Is it lawful?**
Yes. Accessing publicly available web data without bypassing security controls is lawful.

## 2. Necessity Test
**Is the processing necessary to achieve the objective?**
Yes. An AI SEO Specialist cannot audit a website without reading its HTML. An AI Competitor Analyst cannot detect pricing changes without scanning a pricing page. The data extraction is targeted strictly to URLs provided by our clients or discovered via search.

**Can it be achieved in a less intrusive way?**
We have implemented the least intrusive method possible:
*   We use the `urllib.robotparser` to ensure we never access sites that have opted out.
*   We run an automated PII stripping pipeline (Regex masking for emails and phone numbers) to ensure personal data is actively rejected from our system.

## 3. Balancing Test
**Do the individual's rights override the legitimate interest?**
No. Because we strictly target corporate domains for B2B analysis, and actively strip unstructured PII (like employee emails or customer phone numbers) *before* the data reaches the AI context window or persistent storage, the privacy impact on individuals is negligible. 

Webmasters retain full control over their data via the `robots.txt` standard, satisfying the "opt-out" requirements of the EU AI Act (TDM exception).

**Conclusion:** The legitimate interest is valid, necessary, and sufficiently balanced with strict data minimization safeguards.
