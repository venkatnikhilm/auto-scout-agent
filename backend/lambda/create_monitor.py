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
        resp = genai_client.generate(model="gemini-1.5-pro", prompt=prompt, max_output_tokens=10)
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
    url = body.get("url")
    description = body.get("description", "")

    if not url:
        return {"statusCode": 400, "body": json.dumps({"error": "url required"})}

    # avoid duplicates
    existing = get_monitor_by_url(url)
    if existing:
        return {"statusCode": 200, "body": json.dumps({"message": "Monitor already exists", "item": existing})}

    interval_seconds = parse_interval(description)

    item = create_monitor_item(url, description, interval_seconds)

    # start step function execution; pass url & monitor_id
    input_payload = {"url": url, "monitor_id": item["monitor_id"], "description": description}
    sfn.start_execution(stateMachineArn=STEP_FUNCTION_ARN, input=json.dumps(input_payload))

    return {"statusCode": 200, "body": json.dumps({"message": "Monitor created", "monitor": item})}
