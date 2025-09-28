# # backend/db/dynamo_client.py
# import boto3
# import time
# import uuid
# from boto3.dynamodb.conditions import Key
# try:
#     from backend.utils.env import DYNAMO_TABLE, AWS_REGION
# except ImportError:
#     from utils.env import DYNAMO_TABLE, AWS_REGION

# dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
# table = dynamodb.Table(DYNAMO_TABLE)


# def create_monitor_item(url, description, interval_seconds, condition, monitor_id=None):
#     item_id = monitor_id or str(uuid.uuid4())   # ✅ use provided id if available
#     now = int(time.time())
#     item = {
#         "monitor_id": item_id,
#         "url": url,
#         "description": description,
#         "interval_seconds": interval_seconds,
#         "last_price": None,
#         "last_checked": None,
#         "created_at": now,
#         "condition": condition
#     }
#     table.put_item(Item=item)
#     return item


# def get_monitor_by_url(url):
#     resp = table.scan(
#         FilterExpression=Key('url').eq(url)
#     )
#     items = resp.get("Items", [])
#     return items[0] if items else None


# def get_monitor_by_id(monitor_id):
#     resp = table.get_item(Key={"monitor_id": monitor_id})
#     return resp.get("Item")


# def update_monitor_price(monitor_id, price, confidence=None):
#     now = int(time.time())
#     expr = "SET last_price = :p, last_checked = :t"
#     values = {":p": price, ":t": now}
#     table.update_item(
#         Key={"monitor_id": monitor_id},
#         UpdateExpression=expr,
#         ExpressionAttributeValues=values,
#     )
# backend/db/dynamo_client.py
import boto3
import time
import uuid
from boto3.dynamodb.conditions import Key
try:
    from backend.utils.env import DYNAMO_TABLE, AWS_REGION
except ImportError:
    from utils.env import DYNAMO_TABLE, AWS_REGION

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMO_TABLE)

def create_monitor_item(url, description, interval_seconds, condition, monitor_id=None):
    item_id = monitor_id or str(uuid.uuid4())
    now = int(time.time())
    item = {
        "monitor_id": item_id,
        "url": url,
        "description": description,
        "interval_seconds": interval_seconds,
        "last_price": None,
        "last_checked": None,
        "created_at": now,
        "condition": condition,
    }
    table.put_item(Item=item)
    return item

def get_monitor_by_url(url):
    resp = table.scan(FilterExpression=Key('url').eq(url))
    items = resp.get("Items", [])
    return items[0] if items else None

def get_monitor_by_id(monitor_id):
    resp = table.get_item(Key={"monitor_id": monitor_id})
    return resp.get("Item")

def update_monitor_price(monitor_id, price, confidence=None):
    now = int(time.time())
    expr = "SET last_price = :p, last_checked = :t"
    values = {":p": price, ":t": now}
    table.update_item(
        Key={"monitor_id": monitor_id},
        UpdateExpression=expr,
        ExpressionAttributeValues=values
    )