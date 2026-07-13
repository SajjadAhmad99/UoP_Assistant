"""
Shared utilities for UoP Multi-Agent Tools.
Eliminates code duplication across scraper tools.
"""
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
import requests
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup, Tag, NavigableString


@dataclass
class RetrievalResult:
    """Wraps an HTTP response with debug/metrics metadata."""
    url: str = ""
    response: Optional[requests.Response] = None
    success: bool = False
    status_code: int = 0
    latency_ms: float = 0.0
    timestamp: str = ""
    content_length: int = 0
    reliability: str = "UNKNOWN"  # HIGH / MEDIUM / LOW / UNKNOWN
    error_message: str = ""


# ── HTTP Fetch with Retry + Timeout ──────────────────────────────────────────
def safe_get(
    url: str,
    retries: int = 2,
    timeout: int = 10,
    delay_between_retries: float = 2.0
) -> Optional[requests.Response]:
    """
    Robust HTTP GET with retry logic.
    Returns None on total failure instead of raising.

    Args:
        url: URL to fetch
        retries: Number of retry attempts (default 2 for fast failure)
        timeout: Request timeout in seconds (default 10s)
        delay_between_retries: Wait time between retries (default 2s)

    Returns:
        requests.Response or None on failure
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "http://www.uop.edu.pk/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }

    for attempt in range(1, retries + 1):
        try:
            print(f"[{datetime.now()}] HTTP GET attempt {attempt}/{retries}: {url}")
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            print(f"[{datetime.now()}] Timeout on attempt {attempt} for {url}")
        except requests.exceptions.ConnectionError as e:
            print(f"[{datetime.now()}] Connection error on attempt {attempt}: {e}")
        except requests.exceptions.HTTPError as e:
            print(f"[{datetime.now()}] HTTP error on attempt {attempt}: {e}")
            break  # No point retrying HTTP 4xx/5xx errors
        except Exception as e:
            print(f"[{datetime.now()}] Unexpected error: {e}")

        if attempt < retries:
            print(f"[{datetime.now()}] Retrying in {delay_between_retries}s...")
            time.sleep(delay_between_retries)

    print(f"[{datetime.now()}] All {retries} attempts failed for {url}")
    return None


def safe_get_with_metadata(
    url: str,
    retries: int = 2,
    timeout: int = 10,
    delay_between_retries: float = 2.0
) -> RetrievalResult:
    """
    Enhanced HTTP GET that returns a RetrievalResult with full metadata
    for the debug/metrics pipeline.
    """
    result = RetrievalResult(url=url, timestamp=datetime.now().isoformat())
    start_time = time.time()

    response = safe_get(url, retries=retries, timeout=timeout,
                        delay_between_retries=delay_between_retries)

    elapsed_ms = (time.time() - start_time) * 1000
    result.latency_ms = round(elapsed_ms, 1)

    if response is not None:
        result.response = response
        result.success = True
        result.status_code = response.status_code
        result.content_length = len(response.text)
        # Reliability scoring
        if response.status_code == 200 and result.content_length > 500:
            result.reliability = "HIGH"
        elif response.status_code == 200:
            result.reliability = "MEDIUM"
        else:
            result.reliability = "LOW"
    else:
        result.success = False
        result.reliability = "LOW"
        result.error_message = f"All {retries} attempts failed"

    return result


# ── BeautifulSoup Helpers ───────────────────────────────────────────────────
def safe_text(element: Any) -> str:
    """Safely extract text from BeautifulSoup element."""
    if isinstance(element, (Tag, NavigableString)):
        return element.get_text(strip=True)
    return ""


def safe_attr(element: Any, attr: str, default: str = "") -> str:
    """Safely extract attribute from BeautifulSoup Tag."""
    if isinstance(element, Tag):
        value = element.get(attr, default)
        return value if isinstance(value, str) else default
    return default


def build_absolute_url(href: str, base_url: str = "http://www.uop.edu.pk/") -> str:
    """Convert relative URL to absolute."""
    if not href:
        return base_url
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    if href.startswith("?q="):
        return base_url + href
    return base_url + href


# ── Site Unavailable Messages ───────────────────────────────────────────────
SITE_UNAVAILABLE_MSG = (
    "SITE_UNAVAILABLE: The University of Peshawar website (www.uop.edu.pk) "
    "is currently unreachable. This is likely a temporary network issue. "
    "Please try again in a few minutes or visit http://www.uop.edu.pk directly."
)

NO_DATA_FOUND_MSG = (
    "NO_DATA_FOUND: The page loaded but contained no data. "
    "Do not generate any names, titles, or information from memory."
)


# ── Intent Classification Keywords (for reference - crew.py has its own) ───
# These are kept for backward compatibility and tool-level classification
NEWS_KEYWORDS: Set[str] = {
    "news", "announcement", "scholarship", "tender", "job", "opening",
    "event", "notice", "merit list", "deadline", "tenders", "vacancy",
    "admission notice", "result", "date sheet"
}

DEPT_KEYWORDS: Set[str] = {
    "department", "faculty", "program", "professors", "programme", "teacher",
    "lecturer", "subject", "course", "institute", "computer science", "physics",
    "chemistry", "botany", "mathematics", "english", "economics", "history",
    "statistics", "zoology", "geology", "pharmacy", "law", "education",
    "islamic", "urdu", "pashto", "sociology", "journalism", "psychology",
    "political", "geography", "library", "architecture", "fine arts", "sports",
    "dean", "chairman", "hod", "faculty member", "researcher", "lab"
}

HOMEPAGE_KEYWORDS: Set[str] = {
    "vice chancellor", "vc", "registrar", "chancellor", "contact", "address",
    "phone", "email", "location", "office", "homepage", "pro vice chancellor",
    "pro-vice chancellor", "treasurer", "controller", "examinations"
}

FEE_KEYWORDS: Set[str] = {
    "fee", "fees", "tuition", "cost", "payment", "charges", "semester fee",
    "annual fee", "admission fee", "merit", "eligibility", "criteria",
    "admission", "bs", "ms", "msc", "bsc", "phd", "ma", "mphil", "requirement",
    "qualifying", "minimum marks", "aggregate", "closing merit", "seat"
}


# ── Rate Limit Retry Helper ─────────────────────────────────────────────────
def retry_on_rate_limit(func, max_attempts: int = 3, delay_seconds: int = 10):
    """
    Decorator-free retry wrapper for rate-limited API calls.
    Usage: result = retry_on_rate_limit(lambda: api_call(), max_attempts=3)
    """
    last_error = None
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            last_error = e
            err_msg = str(e).lower()
            if "rate limit" in err_msg and attempt < max_attempts - 1:
                print(f"[{datetime.now()}] Rate limit hit. Waiting {delay_seconds}s for attempt {attempt + 2}...")
                time.sleep(delay_seconds)
            else:
                raise
    raise last_error
