# # app.py
# from fastapi import FastAPI, Request
# from apscheduler.schedulers.background import BackgroundScheduler
# from backend.lambda_fns.create_monitor import parse_interval
# from backend.lambda_fns.check_price import lambda_handler as check_price
# from backend.lambda_fns.notify import lambda_handler as notify
# import uuid, json

# from backend.lambda_fns.create_monitor import parse_interval

# app = FastAPI()
# scheduler = BackgroundScheduler()
# scheduler.start()

# monitors = {}  # in-memory (still writing to Dynamo if you want)

# from backend.utils.extract_fields import extract_fields  # <-- new import

# @app.post("/create_monitor")
# async def api_create_monitor(request: Request):
#     body = await request.json()
#     original_description = body.get("description", "")
#     url = body.get("url")

#     # 🔹 Use Gemini to extract fields
#     parsed = extract_fields(original_description)

#     extracted_description = parsed.get("description", original_description)
#     condition = parsed.get("condition", body.get("condition", ""))
#     interval_seconds = parse_interval(parsed.get("interval") or original_description)
#     url = parsed.get("url") if parsed.get("url") and parsed.get("url") != "none" else body.get("url")

#     # generate monitor_id (still stored in memory here, but could also persist to Dynamo)
#     monitor_id = str(uuid.uuid4())

#     monitors[monitor_id] = {
#         "url": url,
#         "description": extracted_description,
#         "condition": condition,
#         "interval_seconds": interval_seconds,
#     }
#     item = create_monitor_item(
#     url,
#     extracted_description,
#     interval_seconds,
#     condition,
#     monitor_id=monitor_id
# )

#     # schedule check_price automatically
#     input_payload = {
#     "url": url,
#     "monitor_id": monitor_id,
#     "description": extracted_description,
#     "condition": condition,
# }

#     scheduler.add_job(
#         check_price,
#         "interval",
#         seconds=interval_seconds,
#         args=[input_payload, None],
#         id=monitor_id,
#         replace_existing=True
#     )

#     return {
#         "message": "Monitor created",
#         "monitor_id": monitor_id,
#         "interval": interval_seconds,
#         "parsed": parsed  # 👀 helpful to debug what Gemini extracted
#     }
# @app.post("/check_price")
# async def api_check_price(request: Request):
#     body = await request.json()
#     result = check_price(body, None)
#     return result

# @app.post("/notify")
# async def api_notify(request: Request):
#     body = await request.json()
#     result = notify(body, None)
#     return result

# @app.get("/")
# def health():
#     return {"status": "ok"}
# backend/app.py
from fastapi import FastAPI, Request
from apscheduler.schedulers.background import BackgroundScheduler

from backend.lambda_fns.create_monitor import parse_interval
from backend.lambda_fns.check_price import lambda_handler as check_price
from backend.lambda_fns.notify import lambda_handler as notify
from backend.db.dynamo_client import create_monitor_item
from backend.utils.extract_fields import extract_fields

import uuid

app = FastAPI()
scheduler = BackgroundScheduler()
scheduler.start()

monitors = {}  # optional: in-memory mirror; DynamoDB is the source of truth

@app.post("/create_monitor")
async def api_create_monitor(request: Request):
    body = await request.json()
    original_description = body.get("description", "")
    url = body.get("url")

    # Use Gemini to extract fields
    parsed = extract_fields(original_description)
    extracted_description = parsed.get("description", original_description)
    condition = parsed.get("condition", body.get("condition", ""))  # body overrides if provided
    interval_seconds = parse_interval(parsed.get("interval") or original_description)
    url = parsed.get("url") if parsed.get("url") and parsed.get("url") != "none" else body.get("url")

    # Generate monitor_id and persist to DynamoDB
    monitor_id = str(uuid.uuid4())
    item = create_monitor_item(
        url=url,
        description=extracted_description,
        interval_seconds=interval_seconds,
        condition=condition,
        monitor_id=monitor_id,  # pass through so check_price can read it later
    )

    # (Optional) keep in-memory mirror for quick debugging
    monitors[monitor_id] = {
        "url": url,
        "description": extracted_description,
        "condition": condition,
        "interval_seconds": interval_seconds,
    }

    # Schedule periodic check
    input_payload = {
        "url": url,
        "monitor_id": monitor_id,
        "description": extracted_description,
        "condition": condition,
    }
    scheduler.add_job(
        check_price,
        "interval",
        seconds=interval_seconds,
        args=[input_payload, None],
        id=monitor_id,
        replace_existing=True,
    )

    return {
        "message": "Monitor created",
        "monitor_id": monitor_id,
        "interval": interval_seconds,
        "parsed": parsed,
    }

@app.post("/check_price")
async def api_check_price(request: Request):
    body = await request.json()
    return check_price(body, None)

@app.post("/notify")
async def api_notify(request: Request):
    body = await request.json()
    return notify(body, None)

@app.get("/")
def health():
    return {"status": "ok"}