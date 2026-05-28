# Data Provenance & Audit Guidelines

To comply with the EU AI Act's Transparency Requirements and general data lineage standards, BengalBound must maintain a verifiable record of where data originated from when scraped by autonomous agents.

## 1. Runtime Extraction Logging
When `agents/toolkit.py:scrape_website` executes, the system must log:
*   **Timestamp:** The exact UTC time of the request.
*   **Source URL:** The exact domain and path.
*   **Agent Identity:** Which agent (e.g., Oracle, Scout) requested the data.
*   **Access Status:** Whether the scrape was successful, or blocked by `robots.txt` / Paywalls.

## 2. PII Quarantine
The data pipeline mandates that no raw scraped data is passed directly to the LLM. 
The `strip_pii()` function is a mandatory gateway. 
*   **Rule:** No email address or phone number from scraped public web data shall be stored in the database or processed by the AI logic models. 

## 3. Training Data Segregation
BengalBound's core business is operational automation, not foundational model training.
However, if scraped data is ever used for LoRA fine-tuning or embedding generation:
*   The data must be cross-referenced with this Audit Log to prove it was not scraped from a domain with a `robots.txt` restriction.
*   An AI Training Transparency Report must be generated summarizing the domains utilized.
