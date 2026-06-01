"""
Universal LangChain tools available to every agent: web search, scraping, API calls.
"""
import logging
import re
import time
import requests
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

USER_AGENT = "BengalBoundBot/1.0 (+https://bengalbound.com/bot-policy)"


def _strip_pii(text: str) -> str:
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED_EMAIL]', text)
    text = re.sub(r'\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\b',
                  '[REDACTED_PHONE]', text)
    return text


def _check_robots(url: str) -> tuple:
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        resp = requests.get(robots_url, headers={"User-Agent": USER_AGENT}, timeout=5)
        if resp.status_code == 200:
            rp.parse(resp.text.splitlines())
            return rp.can_fetch(USER_AGENT, url), min(rp.crawl_delay(USER_AGENT) or 0, 10)
        return True, 0
    except Exception:
        return True, 0


@tool
def search_web(query: str) -> str:
    """Search the internet for real-time information, current news, and facts."""
    try:
        from duckduckgo_search import DDGS
        results = DDGS().text(query, max_results=5)
        if not results:
            return "No results found."
        parts = [
            f"Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}"
            for r in results
        ]
        return _strip_pii("\n\n".join(parts))
    except Exception as e:
        logger.error("search_web failed: %s", e)
        return f"Error performing web search: {e}"


@tool
def scrape_website(url: str) -> str:
    """Scrape the text content of a specific website URL, respecting robots.txt."""
    try:
        allowed, delay = _check_robots(url)
        if not allowed:
            return f"Error: Blocked by robots.txt for {url}"
        if delay:
            time.sleep(delay)
        response = requests.get(url, timeout=15, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        for el in soup(["script", "style", "header", "footer", "nav"]):
            el.decompose()
        return _strip_pii(soup.get_text(separator="\n", strip=True))[:5000]
    except Exception as e:
        logger.error("scrape_website failed: %s", e)
        return f"Error scraping website: {e}"


@tool
def call_api(url: str, method: str = "GET", payload: str = "") -> str:
    """Make an HTTP request to a REST API endpoint and return the response text."""
    try:
        import json
        kwargs: dict = {"timeout": 15, "headers": {"User-Agent": USER_AGENT}}
        if payload:
            kwargs["json"] = json.loads(payload)
        response = requests.request(method.upper(), url, **kwargs)
        return _strip_pii(response.text)[:5000]
    except Exception as e:
        logger.error("call_api failed: %s", e)
        return f"Error calling API: {e}"


def get_universal_tools() -> list:
    """Return all universal tools available to every agent."""
    return [search_web, scrape_website, call_api]
