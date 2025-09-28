# backend/lambda/notify.py
import json
import boto3
import os
try:
    from backend.utils.env import AWS_REGION
except ImportError:
    from utils.env import AWS_REGION

sns = boto3.client("sns", region_name=AWS_REGION)

def lambda_handler(event, context):
    """
    Accepts event with {subject, message, phone_number/email optional}
    For hackathon, publish to preconfigured SNS topic (SMS/email).
    """
    subject = event.get("subject", "AutoScout Notification")
    message = event.get("message") or json.dumps(event)
    sns.publish(TopicArn=os.environ.get("SNS_TOPIC_ARN"), Message=message, Subject=subject)
    return {"status": "sent"}
