# backend/scraper/scraper.py
import requests
from lxml import etree, html
import logging
import time

# If you plan to use Playwright or Selenium, ensure Chrome + driver in your Lambda image and import here.

def fetch_page_html_requests(url, timeout=15):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AutoScout/1.0; +https://example.com/bot)"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def extract_with_xpath(html_text, xpath_expr):
    tree = html.fromstring(html_text)
    nodes = tree.xpath(xpath_expr)
    if not nodes:
        return None
    # return text of first node (handle attributes)
    node = nodes[0]
    if hasattr(node, 'text_content'):
        return node.text_content().strip()
    try:
        return str(node)
    except Exception:
        return None


# Optional: Selenium/Playwright fallback (requires browser in container)
def fetch_page_html_with_browser(url):
    # Minimal example using Playwright sync API (ensure playwright is installed & browsers installed)
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        raise RuntimeError("Playwright not available in this runtime") from e

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=30000)
        content = page.content()
        browser.close()
    return content
