# backend/lambda/check_price.py (modified)
import json
import traceback
import boto3
try:
    from backend.db.dynamo_client import get_monitor_by_id, update_monitor_price
    from backend.scrapper.scraper import fetch_page_html_requests, extract_with_xpath, fetch_page_html_with_browser, fetch_screenshot_playwright
    from backend.agents.data_extractor import extract_from_text, extract_from_image
    from backend.utils.env import SNS_TOPIC_ARN, AWS_REGION
except ImportError:
    # For Lambda deployment, imports might be different
    from db.dynamo_client import get_monitor_by_id, update_monitor_price
    from scrapper.scraper import fetch_page_html_requests, extract_with_xpath, fetch_page_html_with_browser, fetch_screenshot_playwright
    from agents.data_extractor import extract_from_text, extract_from_image
    from utils.env import SNS_TOPIC_ARN, AWS_REGION
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
sns = boto3.client("sns", region_name=AWS_REGION)


def safe_get_html(url):
    try:
        return fetch_page_html_requests(url)
    except Exception as e:
        logger.warning("requests fetch failed: %s; browser fallback", e)
        try:
            return fetch_page_html_with_browser(url)
        except Exception as e2:
            logger.error("browser fetch failed too: %s", e2)
            raise e2


def publish_notification(monitor, old_price, new_price, confidence):
    msg = {
        "title": f"Monitor update: {monitor['description']}",
        "url": monitor["url"],
        "old_price": old_price,
        "new_price": new_price,
        "confidence": confidence,
        "monitor_id": monitor["monitor_id"]
    }
    sns.publish(TopicArn=SNS_TOPIC_ARN, Message=json.dumps(msg), Subject="AutoScout Alert")


def lambda_handler(event, context):
    """
    Input: {"url": "...", "monitor_id": "...", "description": "..."}
    Output: {"interval_seconds": n, "status": "..."}
    """
    try:
        logger.info("check_price started event=%s", json.dumps(event))
        url = event.get("url")
        monitor_id = event.get("monitor_id")

        monitor = get_monitor_by_id(monitor_id)
        if not monitor:
            logger.error("monitor not found: %s", monitor_id)
            return {"interval_seconds": 7200, "status": "monitor_not_found"}

        html_text = None
        try:
            html_text = safe_get_html(url)
        except Exception:
            logger.exception("Failed to fetch HTML")
            # still try screenshot fallback
            html_text = None

        # 1) Primary attempt: ask Gemini to extract from HTML/text
        extracted = None
        if html_text:
            extracted = extract_from_text(html_text, monitor["description"])

        # 2) If low confidence or no value, try screenshot-based extraction (visual)
        if (not extracted) or (extracted.get("confidence", 0.0) < 0.45) or (not extracted.get("value")):
            logger.info("Text extraction low-confidence; trying screenshot extraction")
            try:
                image_bytes = fetch_screenshot_playwright(url)
                extracted_img = extract_from_image(image_bytes, monitor["description"])
                # prefer image extraction if confidence higher
                if extracted_img and extracted_img.get("confidence", 0.0) > extracted.get("confidence", 0.0) if extracted else True:
                    extracted = extracted_img
            except Exception as e:
                logger.warning("Screenshot extraction failed: %s", e)

        # Final normalization/cleanup
        new_value = None
        new_norm = None
        confidence = 0.0
        if extracted and extracted.get("value"):
            new_value = str(extracted.get("value")).strip()
            new_norm = extracted.get("normalized")
            confidence = float(extracted.get("confidence", 0.0))
        else:
            # nothing extracted
            new_value = None
            new_norm = None
            confidence = 0.0

        old_price = monitor.get("last_price")
        # decide changed: compare normalized if available, else string compare
        changed = False
        if new_norm is not None and monitor.get("last_price") is not None:
            try:
                old_norm = float(monitor.get("last_price"))
                changed = (float(new_norm) != old_norm)
            except Exception:
                changed = (new_value != old_price)
        else:
            changed = (new_value and new_value != old_price)

        if new_value and changed:
            publish_notification(monitor, old_price, new_value, confidence)
            update_monitor_price(monitor_id, new_value, confidence)
            logger.info("Change detected for %s: %s -> %s", url, old_price, new_value)
        else:
            # update timestamp even if unchanged
            update_monitor_price(monitor_id, monitor.get("last_price"), confidence)
            logger.info("No change for %s (last=%s)", url, old_price)

        return {"interval_seconds": monitor.get("interval_seconds", 7200), "status": "checked"}
    except Exception:
        logger.error("check_price exception: %s", traceback.format_exc())
        return {"interval_seconds": 7200, "status": "error"}
