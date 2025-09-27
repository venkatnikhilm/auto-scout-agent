# backend/lambda/check_price.py
import json
import traceback
import boto3
from backend.db.dynamo_client import get_monitor_by_id, update_monitor_price
from backend.scraper.scraper import fetch_page_html_requests, extract_with_xpath, fetch_page_html_with_browser
from backend.agents.xpath_agent import ask_gemini_for_xpath
from backend.utils.env import SNS_TOPIC_ARN, AWS_REGION
import logging
from lxml import html

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns = boto3.client("sns", region_name=AWS_REGION)


def safe_get_html(url):
    try:
        return fetch_page_html_requests(url)
    except Exception as e:
        logger.warning(f"requests fetch failed: {e}, trying browser")
        try:
            return fetch_page_html_with_browser(url)
        except Exception as e2:
            logger.error("browser fetch failed too")
            raise e2


def publish_notification(monitor, old_price, new_price):
    msg = {
        "title": f"Monitor update: {monitor['description']}",
        "url": monitor["url"],
        "old_price": old_price,
        "new_price": new_price,
        "monitor_id": monitor["monitor_id"]
    }
    sns.publish(TopicArn=SNS_TOPIC_ARN, Message=json.dumps(msg), Subject="AutoScout Alert")


def lambda_handler(event, context):
    """
    Expected input (from Step Function): {"url": "...", "monitor_id": "...", "description": "..."}
    Must return {"interval_seconds": <n>, ...}
    """
    try:
        logger.info("check_price started with event: %s", json.dumps(event))
        url = event.get("url")
        monitor_id = event.get("monitor_id")

        monitor = get_monitor_by_id(monitor_id)
        if not monitor:
            return {"interval_seconds": 7200, "status": "monitor_not_found"}

        html_text = safe_get_html(url)

        # try existing XPath stored in Dynamo (if any)
        xpath_expr = monitor.get("xpath")
        price_text = None
        if xpath_expr:
            try:
                price_text = extract_with_xpath(html_text, xpath_expr)
            except Exception:
                price_text = None

        # if no price found, ask Gemini to propose an XPath
        if not price_text:
            try:
                xpath_expr = ask_gemini_for_xpath(html_text, monitor["description"])
                # try to extract with suggested xpath
                price_text = extract_with_xpath(html_text, xpath_expr)
                # save the xpath back into the monitor for next run
                # update Dynamo with xpath field (simple update)
                # We'll reuse update_monitor_price to update price, and do separate update for xpath if needed
                from backend.db.dynamo_client import table
                table.update_item(
                    Key={"monitor_id": monitor_id},
                    UpdateExpression="SET xpath = :x",
                    ExpressionAttributeValues={":x": xpath_expr}
                )
            except Exception as e:
                logger.error("Gemini xpath extraction failed: %s", e)
                price_text = None

        # Basic normalization: strip currency symbols / whitespace
        if price_text:
            cleaned = price_text.strip()
            # remove newlines and multiple spaces
            cleaned = " ".join(cleaned.split())
        else:
            cleaned = None

        old_price = monitor.get("last_price")
        new_price = cleaned

        if new_price and new_price != old_price:
            # notify
            publish_notification(monitor, old_price, new_price)
            update_monitor_price(monitor_id, new_price)
            logger.info("Price changed for %s: %s -> %s", url, old_price, new_price)
        else:
            # just update last_checked timestamp if desired
            update_monitor_price(monitor_id, monitor.get("last_price"))
            logger.info("No change for %s (last=%s)", url, old_price)

        # return interval_seconds for Step Function dynamic wait
        return {"interval_seconds": monitor.get("interval_seconds", 7200), "status": "checked"}
    except Exception as e:
        logger.error("check_price exception: %s", traceback.format_exc())
        return {"interval_seconds": 7200, "status": "error"}
