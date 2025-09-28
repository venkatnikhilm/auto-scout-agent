# backend/utils/extract_fields.py
import json
from google import genai

from backend.utils.env import GEMINI_API_KEY

genai_client = genai.Client(api_key=GEMINI_API_KEY)


def extract_fields(original_description: str):
    """
    Uses Gemini to parse user description into structured fields:
    - description
    - interval
    - condition
    - url
    """

    prompt = """You are a structured data extractor.
Analyze the following request and return ONLY a valid JSON object with these keys:
- description: a noun phrase of what is being monitored
- interval: monitoring frequency (e.g. "60 seconds", "2 hours", "daily") or "none"
- condition: trigger condition (e.g. "less than $100", "equal to 'Out of Stock'", "any change")
- url: the full URL if provided, else "none"

Request: """

    try:
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt + original_description
        )

        # try to pull clean text from Gemini response
        text = getattr(resp, "text", "").strip()

        # strip markdown fences if Gemini outputs them
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()

        parsed = json.loads(text)
        return parsed

    except Exception as e:
        # fallback
        return {
            "description": original_description,
            "interval": "",
            "condition": "",
            "url": "none"
        }