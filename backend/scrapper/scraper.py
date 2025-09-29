# backend/scraper/scraper.py
import requests
from lxml import etree, html
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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

# def fetch_screenshot_playwright(url, timeout=30000):
    # """
    # Returns PNG bytes of a full-page screenshot using Playwright.
    # Note: This requires Playwright + browsers installed in your Lambda container.
    # """
    # from playwright.sync_api import sync_playwright
    # with sync_playwright() as p:
    #     browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    #     page = browser.new_page()
    #     page.goto(url, timeout=timeout)
    #     # wait for network idle or small delay if needed
    #     try:
    #         page.wait_for_load_state("networkidle", timeout=5000)
    #     except Exception:
    #         pass
    #     image_bytes = page.screenshot(full_page=True)
    #     browser.close()
    # return image_bytes
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(timeout // 1000)  # Selenium uses seconds
    driver.get(url)

    # Full-page screenshot (Chrome-specific)
    screenshot = driver.get_screenshot_as_png()
    driver.quit()
    return screenshot
def fetch_screenshot_playwright(url, timeout=30000):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(timeout // 1000)
    driver.get(url)

    # 👇 Scroll to bottom to load dynamic content
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # 👇 Resize window to full height before screenshot
    height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1920, height)

    screenshot = driver.get_screenshot_as_png()
    driver.quit()
    return screenshot