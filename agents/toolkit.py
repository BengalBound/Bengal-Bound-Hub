import json
import logging
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

def search_web(query: str, max_results: int = 5) -> str:
    """Search the internet using DuckDuckGo."""
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No results found."
        
        formatted = []
        for r in results:
            formatted.append(f"Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}")
        return "\n\n".join(formatted)
    except Exception as e:
        logger.error(f"search_web failed: {e}")
        return f"Error performing web search: {str(e)}"

def scrape_website(url: str) -> str:
    """Scrape and extract text from a website."""
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BengalBound/1.0"})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove scripts, styles, and empty elements
        for element in soup(["script", "style", "header", "footer", "nav"]):
            element.decompose()
            
        text = soup.get_text(separator="\n", strip=True)
        # Limit to first ~5000 chars to avoid blowing up context window
        return text[:5000]
    except Exception as e:
        logger.error(f"scrape_website failed for {url}: {e}")
        return f"Error scraping website: {str(e)}"

def call_api(url: str, method: str = "GET", payload: str = None) -> str:
    """Generic tool to call an unauthenticated REST API."""
    try:
        kwargs = {"timeout": 15}
        if payload:
            kwargs["json"] = json.loads(payload)
            
        response = requests.request(method.upper(), url, **kwargs)
        return response.text[:5000]
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
