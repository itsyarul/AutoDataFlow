# src/scraper/playwright_client.py
"""
Playwright renderer + heuristic grid/table extractor.

Returns a list of dicts: [{ "headers": [...], "rows": [[...], ...] }, ...]
Designed to detect:
 - native <table> elements
 - semantic grids (role="grid", role="table")
 - popular DataGrid libraries (ag-Grid, MUI, AntD, React Table hints)
 - div-based CSS Grid / Flexbox repeated-row patterns (heuristic)
 - virtualized containers by scrolling their viewport
"""

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from typing import List, Dict, Any, Optional
import time
import re
import logging

logger = logging.getLogger(__name__)

DEFAULT_NAV_TIMEOUT = 15000  # ms
SCROLL_STEP = 400
SCROLL_WAIT = 0.12

GRID_HINTS = [
    "ag-",
    "MuiDataGrid",
    "ant-table",
    "rt-",
    "react-table",
    "data-grid",
    "datagrid",
    "grid-table",
    "table-wrapper",
    "table-responsive",
]


def _matches_grid_hint(el_class: str) -> bool:
    if not el_class:
        return False
    for hint in GRID_HINTS:
        if hint.lower() in el_class.lower():
            return True
    return False


def _extract_from_rows_js():
    # JS used to extract rows given a container handle (passed from page.evaluate)
    return """
    (container) => {
      function getText(e) {
        if (!e) return "";
        if (e.getAttribute && e.getAttribute('aria-label')) return e.getAttribute('aria-label').trim();
        if (e.getAttribute && e.getAttribute('title')) return e.getAttribute('title').trim();
        if (e.alt) return e.alt.trim();
        return (e.textContent || "").trim();
      }
      const rows = [];
      let headers = [];
      // try thead first
      const thead = container.querySelector('thead');
      if (thead) {
        headers = Array.from(thead.querySelectorAll('th')).map(getText).filter(Boolean);
      }
      const possibleRows = Array.from(container.children).filter(c => c.children && c.children.length > 0);
      if (possibleRows.length === 0) {
        const desc = Array.from(container.querySelectorAll(':scope > * > *')).filter(c => c.children && c.children.length > 0);
        possibleRows.push(...desc);
      }
      for (let i = 0; i < Math.min(500, possibleRows.length); i++) {
        const r = possibleRows[i];
        const cells = Array.from(r.children).map(getText);
        if (cells.every(c => c === "")) continue;
        rows.push(cells);
      }
      return { headers, rows };
    }
    """


def _find_candidate_containers(page):
    """
    Heuristic: return element handles that look like repeated-row containers.
    We try semantic selectors first, then a heuristic scan for elements with many children
    and consistent child-child counts.
    """
    candidates = []
    selectors = [
        "table",
        "[role=table]",
        "[role=grid]",
        "[data-testid='DataGrid']",
        ".ag-root",
        ".ant-table",
        ".MuiDataGrid-root",
        ".rt-table",
        ".ReactTable",
    ]
    for sel in selectors:
        try:
            elems = page.query_selector_all(sel)
            for e in elems:
                candidates.append(e)
        except Exception:
            pass

    # Heuristic pass: find containers with many children and a dominant child-child-count
    try:
        script = """
        () => {
          const out = [];
          function nodeId(el) {
            if (!el) return null;
            let path = el.tagName.toLowerCase();
            if (el.id) path += '#' + el.id;
            else if (el.className) path += '.' + (el.className.split(' ').join('.'));
            return path;
          }
          const all = Array.from(document.querySelectorAll('body *'));
          for (let el of all) {
            if (!el.children || el.children.length < 4) continue;
            const counts = Array.from(el.children).map(c => c.children ? c.children.length : 0);
            const freq = {};
            counts.forEach(c => freq[c] = (freq[c] || 0) + 1);
            const maxFreq = Math.max(...Object.values(freq));
            if (maxFreq >= Math.max(4, Math.floor(el.children.length * 0.6))) {
              out.push(nodeId(el));
              if (out.length > 12) break;
            }
          }
          return Array.from(new Set(out));
        }
        """
        hints = page.evaluate(script)
        for p in hints:
            try:
                handle = page.query_selector(p)
                if handle:
                    candidates.append(handle)
            except Exception:
                pass
    except Exception:
        pass

    # dedupe by outerHTML prefix
    uniq = []
    seen = set()
    for h in candidates:
        try:
            marker = h.evaluate("el => (el.outerHTML||'').slice(0,200)")
        except Exception:
            marker = None
        if marker and marker not in seen:
            seen.add(marker)
            uniq.append(h)
    return uniq


def _scroll_container_collect(page, container_selector: str, max_scrolls=30):
    """
    Scroll the container to reveal virtualized rows and collect rows via JS.
    Returns list of row arrays.
    """
    js = """
    (selector, step, maxSteps) => {
      const el = document.querySelector(selector) || document.querySelector(selector.replace(/\\./g, ' '));
      if (!el) return [];
      const out = [];
      function collect() {
        const rows = [];
        for (const r of el.children) {
          const cells = [];
          for (const c of r.children) {
            const text = (c.getAttribute && c.getAttribute('aria-label')) || c.title || c.innerText || c.textContent || "";
            cells.push((text||'').trim());
          }
          if (cells.length > 0 && cells.some(t => t && t.length > 0)) rows.push(cells);
        }
        return rows;
      }
      for (let i = 0; i < maxSteps; i++) {
        const snap = collect();
        if (snap.length > 0) out.push(...snap);
        el.scrollBy(0, step);
      }
      return out;
    }
    """
    try:
        rows = page.evaluate(js, container_selector, SCROLL_STEP, max_scrolls)
        return rows
    except Exception:
        return []


def extract_grid_tables_from_page(page, wait_for=1200) -> List[Dict[str, Any]]:
    """
    Extract multiple possible tables/grids from a rendered Playwright page.
    Returns list of { headers: [...], rows: [[...], ...] } dicts.
    """
    results = []
    try:
        time.sleep(wait_for / 1000.0)
    except Exception:
        pass

    # 1) Native <table> (useful for pages that render <table> via JS)
    try:
        tables = page.query_selector_all("table")
        for t in tables:
            try:
                r = page.evaluate(
                    """(table) => {
                      function getText(e){ return (e && e.textContent) ? e.textContent.trim() : ''; }
                      const headers = [];
                      const thead = table.querySelector('thead');
                      if (thead) {
                        for (const th of thead.querySelectorAll('th')) headers.push(getText(th));
                      } else {
                        const firstThs = table.querySelectorAll('tr:first-child th');
                        if (firstThs && firstThs.length) for (const th of firstThs) headers.push(getText(th));
                      }
                      const rows = [];
                      for (const tr of table.querySelectorAll('tbody tr')) {
                        const cells = Array.from(tr.children).map(getText);
                        rows.push(cells);
                      }
                      return { headers, rows };
                    }""",
                    t,
                )
                if r and (r.get("rows") or r.get("headers")):
                    results.append(r)
            except Exception:
                pass
    except Exception:
        pass

    # 2) semantic grids / popular libraries
    sem_selectors = ["[role=grid]", "[role=table]", "[data-testid='DataGrid']", ".MuiDataGrid-root", ".ag-root", ".ant-table"]
    for sel in sem_selectors:
        try:
            elems = page.query_selector_all(sel)
            for el in elems:
                try:
                    r = page.evaluate(_extract_from_rows_js(), el)
                except Exception:
                    try:
                        r = page.evaluate(
                            """(container) => {
                              const getText = (e) => (e.getAttribute && e.getAttribute('aria-label')) || e.title || e.innerText || e.textContent || '';
                              const headers = [];
                              const firstRow = container.querySelector(':scope > *');
                              if (firstRow) {
                                const maybe = Array.from(firstRow.children).map(getText);
                                if (maybe.filter(Boolean).length > 0) headers.push(...maybe);
                              }
                              const rows = [];
                              for (const r of container.children) {
                                const cells = Array.from(r.children).map(getText).map(s => s.trim());
                                if (cells.some(c => c && c.length > 0)) rows.push(cells);
                              }
                              return { headers, rows };
                            }""",
                            el,
                        )
                    except Exception:
                        r = None
                if r and r.get("rows"):
                    results.append(r)
        except Exception:
            pass

    # 3) heuristic div-based containers
    try:
        candidates = _find_candidate_containers(page)
        for c in candidates:
            try:
                r = page.evaluate(_extract_from_rows_js(), c)
            except Exception:
                try:
                    r = page.evaluate(
                        """(container) => {
                          const getText = e => (e && e.innerText) ? e.innerText.trim() : '';
                          const rows = [];
                          const headers = [];
                          const children = Array.from(container.children);
                          if (children.length > 0) {
                            const first = children[0];
                            const firstCells = Array.from(first.children).map(getText);
                            if (firstCells.every(c => c.length > 0 && c.length < 160) && firstCells.length >= 2) {
                              headers.push(...firstCells);
                              for (let i = 1; i < children.length; i++) {
                                const r = Array.from(children[i].children).map(getText);
                                if (r.some(x => x && x.length > 0)) rows.push(r);
                              }
                            } else {
                              for (const ch of children) {
                                const r = Array.from(ch.children).map(getText);
                                if (r.some(x => x && x.length > 0)) rows.push(r);
                              }
                            }
                          }
                          return { headers, rows };
                        }""",
                        c,
                    )
                except Exception:
                    r = None
            if r and r.get("rows"):
                if not r.get("headers"):
                    max_cols = max((len(row) for row in r["rows"]), default=0)
                    r["headers"] = [f"col_{i+1}" for i in range(max_cols)]
                results.append(r)
    except Exception:
        pass

    # 4) virtualized grids: attempt to scroll known viewport selectors
    try:
        virtual_selectors = [
            ".ag-body-viewport",
            ".ReactVirtualized__Grid",
            ".ReactVirtualized__List",
            ".MuiDataGrid-virtualScroller",
            ".ant-table-body",
            ".rt-tbody",
            ".data-grid",
            ".table-scroll",
            ".table-container",
        ]
        for sel in virtual_selectors:
            try:
                if page.query_selector(sel):
                    rows = _scroll_container_collect(page, sel, max_scrolls=60)
                    if rows:
                        max_cols = max((len(r) for r in rows), default=0)
                        headers = [f"col_{i+1}" for i in range(max_cols)]
                        results.append({"headers": headers, "rows": rows})
            except Exception:
                pass
    except Exception:
        pass

    # dedupe by (headers length, rows length)
    uniq = []
    seen_sig = set()
    for r in results:
        try:
            sig = (len(r.get("headers", [])), len(r.get("rows", [])))
        except Exception:
            sig = None
        if sig not in seen_sig:
            seen_sig.add(sig)
            uniq.append(r)
    return uniq


# ... (imports)
import atexit

# Global Browser Manager
class BrowserManager:
    _instance = None
    
    def __init__(self):
        self._playwright = None
        self._browser = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_browser(self):
        """Lazy initialization of the browser."""
        if self._browser is None:
            from playwright.sync_api import sync_playwright
            logger.info("Starting new Playwright browser instance...")
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            atexit.register(self.close)
        return self._browser

    def close(self):
        if self._browser:
            logger.info("Closing Playwright browser...")
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

_manager = BrowserManager.get_instance()

def render_and_extract(url: str, timeout: int = 30, wait_for: int = 900, proxy: Optional[str] = None, screenshot_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Open page with Playwright and extract grid tables.
    Returns list of {headers, rows}.
    """
    results: List[Dict[str, Any]] = []
    page_content = ""
    
    try:
        browser = _manager.get_browser()
        
        # Configure proxy if provided
        context_args = {}
        if proxy:
            # Parse proxy string "http://user:pass@host:port" or "http://host:port"
            # Playwright expects {server: "...", username: "...", password: "..."}
            from urllib.parse import urlparse
            p = urlparse(proxy)
            proxy_config = {"server": f"{p.scheme}://{p.hostname}:{p.port}"}
            if p.username:
                proxy_config["username"] = p.username
            if p.password:
                proxy_config["password"] = p.password
            context_args["proxy"] = proxy_config
            
        # Create a new context for this specific job
        context = browser.new_context(**context_args)
        
        # Apply stealth
        try:
            from playwright_stealth import stealth_sync
            page = context.new_page()
            stealth_sync(page)
        except ImportError:
            logger.warning("playwright-stealth not installed, skipping stealth mode")
            page = context.new_page()
            
        page.set_default_navigation_timeout(timeout * 1000)
        
        try:
            try:
                page.goto(url, wait_until="networkidle")
            except PWTimeout:
                logger.info("Playwright navigation timeout for %s", url)
                try:
                    page.goto(url, wait_until="load")
                except Exception:
                    pass
            # Capture content for selectors
            try:
                page_content = page.content()
            except Exception:
                page_content = ""
                
            # best-effort extraction
            results = extract_grid_tables_from_page(page, wait_for=wait_for)
        except Exception as exc:
            logger.exception("render_and_extract failed: %s", exc)
            if screenshot_path:
                try:
                    page.screenshot(path=screenshot_path)
                    logger.info("Saved error screenshot to %s", screenshot_path)
                except Exception:
                    pass
            results = []
        finally:
            try:
                context.close()
            except Exception:
                pass
    except Exception as e:
        logger.exception("Fatal Playwright error: %s", e)
        # Force restart of browser on fatal error
        _manager.close()
        
    return {"tables": results, "content": page_content}

