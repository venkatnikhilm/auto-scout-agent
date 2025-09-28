# backend/lambda/create_monitor.py
import json
import re
import boto3
from backend.db.dynamo_client import create_monitor_item, get_monitor_by_url
from backend.utils.env import STEP_FUNCTION_ARN, DEFAULT_INTERVAL
from google import genai
from backend.utils.env import GEMINI_API_KEY

import os

# instantiate clients
sfn = boto3.client("stepfunctions")
genai_client = genai.Client(api_key=GEMINI_API_KEY)


def parse_interval(description: str) -> int:
    desc = description.lower()
    # quick regex
    m = re.search(r"every\s+(\d+)\s*(minute|hour|second|day)s?", desc)
    if m:
        value = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("second"):
            return max(10, value)
        if unit.startswith("minute"):
            return max(30, value * 60)
        if unit.startswith("hour"):
            return max(60 * 60, value * 3600)
        if unit.startswith("day"):
            return max(24 * 3600, value * 86400)
    # fallback to LLM parse (ask for an integer seconds)
    prompt = (
        f"Extract a monitoring interval in seconds from this short description. "
        f"If no interval specified, return the number  {DEFAULT_INTERVAL}.\n\nDescription: \"{description}\"\n\nReturn only the number."
    )
    try:
        resp = genai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        # extract text safely
        text = ""
        try:
            text = resp.output[0].content[0].text
        except Exception:
            text = getattr(resp, "text", "")
        num = int(re.sub(r"\D", "", text))
        if num <= 0:
            return DEFAULT_INTERVAL
        return num
    except Exception:
        return DEFAULT_INTERVAL


def lambda_handler(event, context):
    """
    Expects event JSON with {"url": ..., "description": ...}
    """
    body = event.get("body")
    if isinstance(body, str):
        body = json.loads(body)
    description = body.get("description", "")
    
    prompt = """You are a structured data extractor. Analyze the following request to identify the specific parameter being monitored, the mandatory notification frequency, the trigger condition, and any provided URL. Format the output as a JSON object with the keys 'description', 'interval', 'condition', and 'url'.
        Formatting Rules:
        'description': A brief, noun-based phrase identifying what is being checked (e.g., 'price of item', 'stock level', 'web page content').
        'interval': The required notification frequency (e.g., '3 hours', 'daily', 'none' if only a condition is set).
        'condition': The trigger for notification (e.g., 'less than $100', 'equal to 'Out of Stock'', 'any change').
        'url': The full URL if provided in the text; otherwise, use the value 'none'.
    """
    description = json.loads(genai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt + "\n\nRequest: " + description).text).get("description", description)
    url = description.get("url")

    if not url:
        return {"statusCode": 400, "body": json.dumps({"error": "url required"})}

    # avoid duplicates
    existing = get_monitor_by_url(url)
    if existing:
        return {"statusCode": 200, "body": json.dumps({"message": "Monitor already exists", "item": existing})}

    interval_seconds = parse_interval(description.get("interval", body.get("description", "")))

    item = create_monitor_item(url, description.get("description", body.get("description", "")), interval_seconds)

    # start step function execution; pass url & monitor_id
    input_payload = {"url": url, "monitor_id": item["monitor_id"], "description": description.get("description", body.get("description", ""))}
    sfn.start_execution(stateMachineArn=STEP_FUNCTION_ARN, input=json.dumps(input_payload))

    return {"statusCode": 200, "body": json.dumps({"message": "Monitor created", "monitor": item})}
