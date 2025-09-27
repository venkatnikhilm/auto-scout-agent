# backend/utils/env.py
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
DYNAMO_TABLE = os.getenv("DYNAMO_TABLE", "PriceMonitor")
STEP_FUNCTION_ARN = os.getenv("STEP_FUNCTION_ARN", "")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_INTERVAL = int(os.getenv("DEFAULT_INTERVAL", "7200"))  # 2 hours