# src/scraper/fetcher.py
import logging
from typing import List, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def fetch_with_requests(url: str, timeout: int = 10, proxies: Optional[dict] = None) -> str:
    """Fetch page HTML with requests (fast). Raise on error."""
    resp = requests.get(url, timeout=timeout, headers=HEADERS, proxies=proxies)
    resp.raise_for_status()
    return resp.text


# keep a simple compatibility wrapper for historic calls that expect raw HTML
def fetch_with_playwright_raw(url: str, timeout: int = 30, wait_for_selector: Optional[str] = None, wait_extra: float = 0.5) -> str:
    """
    Render page with Playwright and return page HTML (raw). This function kept for compatibility.
    """
    from src.scraper.playwright_client import BrowserManager, PWTimeout
    
    manager = BrowserManager.get_instance()
    try:
        browser = manager.get_browser()
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(url, timeout=timeout * 1000)
            if wait_for_selector:
                try:
                    page.wait_for_selector(wait_for_selector, timeout=timeout * 1000)
                except PWTimeout:
                    logger.info("Playwright: selector %s not found within %ss", wait_for_selector, timeout)
                if wait_extra:
                    page.wait_for_timeout(int(wait_extra * 1000))
            return page.content()
        finally:
            try:
                context.close()
            except Exception:
                pass
    except Exception as e:
        logger.error("fetch_with_playwright_raw failed: %s", e)
        raise


def render_and_extract_with_playwright(url: str, timeout: int = 30, wait_for: int = 900, proxy: Optional[str] = None, screenshot_path: Optional[str] = None):
    """
    Import the specialized extractor implemented in playwright_client.
    Returns: {"tables": [...], "content": "..."}
    """
    from src.scraper.playwright_client import render_and_extract
    return render_and_extract(url, timeout=timeout, wait_for=wait_for, proxy=proxy, screenshot_path=screenshot_path)


def extract_tables(html: str) -> List:
    """
    Return a list of pandas DataFrame objects parsed from HTML `<table>` elements.
    """
    from io import StringIO
    import pandas as pd

    soup = BeautifulSoup(html or "", "html.parser")
    tables = soup.find_all("table")
    result = []
    for table in tables:
        try:
            df = pd.read_html(StringIO(str(table)))[0]
            result.append(df)
        except Exception as e:
            logger.debug("Failed to parse a table with pandas: %s", e)
    return result


def extract_table_by_selector(html: str, selector: str) -> List:
    """
    Return a list of DataFrames parsed from elements matching a CSS selector.
    This stays HTML-only (BeautifulSoup + pandas.read_html).
    """
    if not html or not selector:
        return []
    from io import StringIO
    import pandas as pd

    soup = BeautifulSoup(html or "", "html.parser")
    selected = soup.select(selector)
    dfs = []
    for el in selected:
        try:
            df = pd.read_html(StringIO(str(el)))[0]
            dfs.append(df)
        except Exception as e:
            logger.debug("extract_table_by_selector: failed to parse element: %s", e)
            continue
    return dfs


def extract_next_page_link(html: str, base_url: str) -> Optional[str]:
    """
    Attempt to find a 'Next' page link in the HTML.
    Returns absolute URL or None.
    """
    if not html:
        return None
    
    from urllib.parse import urljoin
    soup = BeautifulSoup(html, "html.parser")
    
    # Common text patterns for "Next" buttons
    next_patterns = [
        "next", "Next", "NEXT", ">", "»", "›", "More", "older"
    ]
    
    # 1. Look for <a> tags with rel="next"
    link = soup.find("a", attrs={"rel": "next"})
    if link and link.get("href"):
        return urljoin(base_url, link.get("href"))
        
    # 2. Look for <a> tags containing specific text
    for pattern in next_patterns:
        # strict text match or partial? partial is riskier but more inclusive
        # try exact match first
        link = soup.find("a", string=pattern)
        if link and link.get("href"):
            return urljoin(base_url, link.get("href"))
            
        # try partial match (case insensitive)
        # (be careful not to match "Next Generation" or something unrelated)
        # simple heuristic: text length < 20
        candidates = soup.find_all("a", string=lambda t: t and pattern.lower() in t.lower() and len(t) < 20)
        if candidates:
            return urljoin(base_url, candidates[0].get("href"))
            
    # 3. Look for common class names/IDs
    pagination_classes = ["next", "pagination-next", "nav-next"]
    for cls in pagination_classes:
        link = soup.find("a", class_=cls) or soup.find("a", id=cls)
        if link and link.get("href"):
            return urljoin(base_url, link.get("href"))
            
    return None
