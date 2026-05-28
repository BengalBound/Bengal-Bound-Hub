import json
import logging
import requests
import re
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

# Mandatory Compliance Identity
USER_AGENT = "BengalBoundBot/1.0 (+https://bengalbound.com/bot-policy)"

def strip_pii(text: str) -> str:
    """Aggressive regex to mask PII (emails and phone numbers) to comply with GDPR/DPA."""
    # Mask emails
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    text = re.sub(email_pattern, '[REDACTED_EMAIL]', text)
    
    # Mask standard phone numbers (US/International)
    phone_pattern = r'\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\b'
    text = re.sub(phone_pattern, '[REDACTED_PHONE]', text)
    
    return text

def check_robots_txt(url: str, user_agent: str) -> tuple:
    """Check robots.txt compliance and return (is_allowed, crawl_delay)."""
    try:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = f"{base_url}/robots.txt"
        
        rp = RobotFileParser()
        rp.set_url(robots_url)
        
        robots_resp = requests.get(robots_url, headers={"User-Agent": user_agent}, timeout=5)
        if robots_resp.status_code == 200:
            rp.parse(robots_resp.text.splitlines())
            allowed = rp.can_fetch(user_agent, url)
            # Default to 0 delay if none specified, cap at 10s maximum to prevent blocking AI
            delay = min(rp.crawl_delay(user_agent) or 0, 10)
            return allowed, delay
        return True, 0
    except Exception as e:
        logger.warning(f"Error parsing robots.txt for {url}: {e}")
        return True, 0

def search_web(query: str, max_results: int = 5) -> str:
    """Search the internet using DuckDuckGo."""
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No results found."
        
        formatted = []
        for r in results:
            formatted.append(f"Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}")
        
        # Strip PII from search snippets
        clean_text = strip_pii("\n\n".join(formatted))
        return clean_text
    except Exception as e:
        logger.error(f"search_web failed: {e}")
        return f"Error performing web search: {str(e)}"

def scrape_website(url: str) -> str:
    """Scrape and extract text from a website, strictly adhering to robots.txt and stripping PII."""
    try:
        # 1. Compliance: Check robots.txt (Machine-Readable Exclusion)
        allowed, delay = check_robots_txt(url, USER_AGENT)
        if not allowed:
            logger.info(f"Scrape blocked by robots.txt for {url}")
            return f"Error: Access Denied. The website's robots.txt policy strictly forbids AI scraping for URL: {url}. We must respect this legal boundary."
        
        # 2. Compliance: Politeness Delay
        if delay > 0:
            logger.info(f"Respecting crawl-delay of {delay}s for {url}")
            time.sleep(delay)
            
        # 3. Compliance: Clear Identification
        response = requests.get(url, timeout=15, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        for element in soup(["script", "style", "header", "footer", "nav"]):
            element.decompose()
            
        text = soup.get_text(separator="\n", strip=True)
        
        # 4. Compliance: Automated Content Classification & PII Stripping
        clean_text = strip_pii(text)
        
        return clean_text[:5000]
    except Exception as e:
        logger.error(f"scrape_website failed for {url}: {e}")
        return f"Error scraping website: {str(e)}"

def call_api(url: str, method: str = "GET", payload: str = None) -> str:
    """Generic tool to call an unauthenticated REST API."""
    try:
        kwargs = {"timeout": 15, "headers": {"User-Agent": USER_AGENT}}
        if payload:
            kwargs["json"] = json.loads(payload)
            
        response = requests.request(method.upper(), url, **kwargs)
        clean_text = strip_pii(response.text)
        return clean_text[:5000]
    except Exception as e:
        logger.error(f"call_api failed for {url}: {e}")
        return f"Error calling API: {str(e)}"

# Define the Universal Tools schema for LiteLLM/OpenAI
UNIVERSAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the internet for real-time information, news, and facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_website",
            "description": "Scrape the text content of a specific website URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL of the website to scrape."
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_api",
            "description": "Make an HTTP request to a REST API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The API endpoint URL."},
                    "method": {"type": "string", "description": "HTTP method (GET, POST, etc.)", "default": "GET"},
                    "payload": {"type": "string", "description": "JSON string of the payload body if method is POST/PUT/etc.", "default": ""}
                },
                "required": ["url"]
            }
        }
    }
]

def execute_tool(tool_name: str, arguments: dict) -> str:
    """Route tool execution to the appropriate function."""
    if tool_name == "search_web":
        return search_web(arguments.get("query"))
    elif tool_name == "scrape_website":
        return scrape_website(arguments.get("url"))
    elif tool_name == "call_api":
        return call_api(arguments.get("url"), arguments.get("method", "GET"), arguments.get("payload"))
    else:
        return f"Error: Tool {tool_name} not found."
