# # backend/lambda/create_monitor.py
# import json
# import re
# import boto3
# try:
#     from backend.db.dynamo_client import create_monitor_item, get_monitor_by_url
#     from backend.utils.env import STEP_FUNCTION_ARN, DEFAULT_INTERVAL, GEMINI_API_KEY
# except ImportError:
#     # For Lambda deployment, imports might be different
#     from db.dynamo_client import create_monitor_item, get_monitor_by_url
#     from utils.env import STEP_FUNCTION_ARN, DEFAULT_INTERVAL, GEMINI_API_KEY
# from google import genai

# import os
# from apscheduler.schedulers.background import BackgroundScheduler
# from backend.lambda_fns.check_price import lambda_handler as check_price

# scheduler = BackgroundScheduler()
# scheduler.start()


# # instantiate clients
# sfn = boto3.client("stepfunctions")
# genai_client = genai.Client(api_key=GEMINI_API_KEY)


# def parse_interval(description: str) -> int:
#     desc = description.lower()
#     # quick regex
#     m = re.search(r"every\s+(\d+)\s*(minute|hour|second|day)s?", desc)
#     if m:
#         value = int(m.group(1))
#         unit = m.group(2)
#         if unit.startswith("second"):
#             return max(10, value)
#         if unit.startswith("minute"):
#             return max(30, value * 60)
#         if unit.startswith("hour"):
#             return max(60 * 60, value * 3600)
#         if unit.startswith("day"):
#             return max(24 * 3600, value * 86400)
#     # fallback to LLM parse (ask for an integer seconds)
#     prompt = (
#         f"Extract a monitoring interval in seconds from this short description. "
#         f"If no interval specified, return the number  {DEFAULT_INTERVAL}.\n\nDescription: \"{description}\"\n\nReturn only the number."
#     )
#     try:
#         resp = genai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
#         # extract text safely
#         text = ""
#         try:
#             text = resp.output[0].content[0].text
#         except Exception:
#             text = getattr(resp, "text", "")
#         num = int(re.sub(r"\D", "", text))
#         if num <= 0:
#             return DEFAULT_INTERVAL
#         return num
#     except Exception:
#         return DEFAULT_INTERVAL


# def lambda_handler(event, context):
#     """
#     Expects event JSON with {"url": ..., "description": ...}
#     """
#     body = event.get("body")
#     if isinstance(body, str):
#         body = json.loads(body)
    
#     original_description = body.get("description", "")
    
#     prompt = """You are a structured data extractor. Analyze the following request to identify the specific parameter being monitored, the mandatory notification frequency, the trigger condition, and any provided URL. Format the output as a JSON object with the keys 'description', 'interval', 'condition', and 'url'.
#         Formatting Rules:
#         'description': A brief, noun-based phrase identifying what is being checked (e.g., 'price of item', 'stock level', 'web page content').
#         'interval': The required notification frequency (e.g., '3 hours', 'daily', 'none' if only a condition is set).
#         'condition': The trigger for notification (e.g., 'less than $100', 'equal to 'Out of Stock'', 'any change').
#         'url': The full URL if provided in the text; otherwise, use the value 'none'.
#     """
    
#     try:
#         # Parse the LLM response properly
#         llm_response = genai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt + "\n\nRequest: " + original_description)
    
    
#     # Extract JSON from markdown code blocks if present
#         response_text = llm_response.text.strip()
#         if response_text.startswith("```json"):
#             # Remove markdown code block markers
#             response_text = response_text.replace("```json", "").replace("```", "").strip()
#         elif response_text.startswith("```"):
#             # Remove generic code block markers
#             response_text = response_text.replace("```", "").strip()
        
#         parsed_data = json.loads(response_text)
        
#         # Extract values from parsed data
#         extracted_description = parsed_data.get("description", original_description)
#         url = parsed_data.get("url")
#         extracted_interval = parsed_data.get("interval", "")
#         condition = parsed_data.get("condition", "")
        
#         # # Handle "none" URL case
#         # if url == "none" or None :
#         #     url = body.get("url")  # Fallback to direct URL from body
            
#     except Exception as e:
#         # Fallback if parsing fails
#         extracted_description = original_description
#         url = body.get("url")
#         extracted_interval = ""

#     if not url:
#         return {"statusCode": 400, "body": json.dumps({"error": "url required"})}

#     # avoid duplicates
#     existing = get_monitor_by_url(url)
#     if existing:
#         return {"statusCode": 200, "body": json.dumps({"message": "Monitor already exists", "item": existing})}

#     # Use extracted interval or fallback to original description
#     interval_seconds = parse_interval(extracted_interval if extracted_interval else original_description)


#     item = create_monitor_item(url, extracted_description, interval_seconds, condition)

#     # start step function execution; pass url & monitor_id
#     input_payload = {"url": url, "monitor_id": item["monitor_id"], "description": extracted_description, "condition": condition}
#     sfn.start_execution(stateMachineArn=STEP_FUNCTION_ARN, input=json.dumps(input_payload))

#     return {"statusCode": 200, "body": json.dumps({"message": "Monitor created", "monitor": item})}


# # if __name__ == "__main__":
# #     test_event = {
# #         "body": {"description": "You need to track the price of the item and notify me when it is less than $100 on the website https://www.nike.com/t/air-foamposite-one-mens-shoes-nrH2sc/HJ5195-400"}
# #     }
# #     print(lambda_handler(test_event, None))

import json
import re
# try:
#     from backend.db.dynamo_client import create_monitor_item, get_monitor_by_url
#     from backend.utils.env import DEFAULT_INTERVAL, GEMINI_API_KEY
# except ImportError:
#     from db.dynamo_client import create_monitor_item, get_monitor_by_url
#     from utils.env import DEFAULT_INTERVAL, GEMINI_API_KEY
from backend.db.dynamo_client import create_monitor_item, get_monitor_by_url
from backend.utils.env import STEP_FUNCTION_ARN, DEFAULT_INTERVAL, GEMINI_API_KEY

from google import genai
from apscheduler.schedulers.background import BackgroundScheduler
from backend.lambda_fns.check_price import lambda_handler as check_price

# global scheduler instance
scheduler = BackgroundScheduler()
scheduler.start()

genai_client = genai.Client(api_key=GEMINI_API_KEY)


def parse_interval(description: str) -> int:
    desc = description.lower()
    m = re.search(r"every\s+(\d+)\s*(minute|hour|second|day)s?", desc)
    if m:
        value = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("second"):
            return max(10, value)
        if unit.startswith("minute"):
            return max(30, value * 60)
        if unit.startswith("hour"):
            return max(3600, value * 3600)
        if unit.startswith("day"):
            return max(86400, value * 86400)

    # fallback: use LLM
    prompt = (
        f"Extract a monitoring interval in seconds from this short description. "
        f"If no interval specified, return {DEFAULT_INTERVAL}.\n\n"
        f"Description: \"{description}\"\n\nReturn only the number."
    )
    try:
        resp = genai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = getattr(resp, "text", "").strip()
        num = int(re.sub(r"\D", "", text))
        return num if num > 0 else DEFAULT_INTERVAL
    except Exception:
        return DEFAULT_INTERVAL


def lambda_handler(event, context):
    body = event.get("body")
    if isinstance(body, str):
        body = json.loads(body)

    original_description = body.get("description", "")

    # Extract structured request with LLM
    try:
        prompt = (
            "You are a structured data extractor..."
            f"\n\nRequest: {original_description}"
        )
        llm_response = genai_client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )

        response_text = llm_response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()

        parsed_data = json.loads(response_text)
        extracted_description = parsed_data.get("description", original_description)
        url = parsed_data.get("url")
        extracted_interval = parsed_data.get("interval", "")
        condition = parsed_data.get("condition", "")
    except Exception:
        extracted_description = original_description
        url = body.get("url")
        extracted_interval = ""
        condition = ""

    if not url:
        return {"statusCode": 400, "body": json.dumps({"error": "url required"})}

    # avoid duplicates
    existing = get_monitor_by_url(url)
    if existing:
        return {"statusCode": 200, "body": json.dumps({"message": "Monitor already exists", "item": existing})}

    interval_seconds = parse_interval(extracted_interval or original_description)
    item = create_monitor_item(url, extracted_description, interval_seconds, condition)

    # schedule recurring job
    input_payload = {
        "url": url,
        "monitor_id": item["monitor_id"],
        "description": extracted_description,
        "condition": condition
    }

    scheduler.add_job(
        check_price,
        "interval",
        seconds=interval_seconds,
        args=[input_payload, None],
        id=item["monitor_id"],
        replace_existing=True
    )

    return {"statusCode": 200, "body": json.dumps({"message": "Monitor created", "monitor": item})}