# backend/agents/data_extractor.py
import re
import json
import logging
from google import genai
try:
    from backend.utils.env import GEMINI_API_KEY
except ImportError:
    from utils.env import GEMINI_API_KEY

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# instantiate Gemini client (adapt if your SDK differs)
genai_client = genai.Client(api_key=GEMINI_API_KEY)


def _resp_to_text(resp):
    """
    Robust extraction of textual content from genai response objects.
    SDK shapes vary across versions; try a couple of common paths.
    """
    try:
        # newer shaped responses
        return resp.text
    except Exception:
        try:
            # older style
            return resp.candidates[0].content
        except Exception:
            try:
                return getattr(resp, "text", "")
            except Exception:
                return ""


def _find_currency_in_text(text: str):
    # match $1,234.56 or €1234 or £1,234 etc
    m = re.search(r"[\$€£]\s*[0-9,]+(?:\.[0-9]+)?", text)
    if m:
        return m.group(0)
    # fallback: naked numbers with decimals (avoid capturing years by heuristic)
    m2 = re.search(r"\b[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?\b", text)
    if m2:
        return m2.group(0)
    return None


def _normalize_number(text: str):
    if not text:
        return None
    # remove currency symbols and commas
    s = re.sub(r"[^\d.\-]", "", text)
    try:
        # prefer float if decimal present otherwise int
        if "." in s:
            return float(s)
        return int(s)
    except Exception:
        return None


def extract_from_text(html_snippet: str, description: str):
    """
    Ask Gemini to extract the target described by `description`
    from the given HTML/text snippet.

    Returns a dict: { "value": str, "normalized": number|None, "confidence": float }
    """
    safe_html = (html_snippet or "")[:100000]  # truncate to be safe for token limits

    prompt = (
        "You are a precise information extraction assistant. "
        "Given a short HTML/text snippet and a user description of a single field to extract, "
        "return a JSON object with these keys:\n"
        '  "value": the extracted value as text (string),\n'
        '  "normalized": a numeric value if appropriate (number) or null,\n'
        '  "confidence": a float between 0.0 and 1.0 indicating how confident you are.\n\n'
        "Return ONLY valid JSON and nothing else.\n\n"
        f"Description: {description}\n\n"
        f"HTML/TEXT:\n{safe_html}\n\n"
    )

    try:
        resp = genai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = _resp_to_text(resp).strip()

        # try to find JSON in the output
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                parsed = json.loads(m.group(0))
                # normalize if possible
                if parsed.get("normalized") is None and parsed.get("value"):
                    parsed["normalized"] = _normalize_number(parsed.get("value"))
                # ensure confidence present
                parsed["confidence"] = float(parsed.get("confidence", 0.8))
                return {
                    "value": parsed.get("value"),
                    "normalized": parsed.get("normalized"),
                    "confidence": parsed.get("confidence")
                }
            except Exception:
                logger.warning("Failed to parse JSON from Gemini response")

        # fallback heuristics: try to extract currency/number from text or html
        candidate = _find_currency_in_text(text) or _find_currency_in_text(safe_html)
        normalized = _normalize_number(candidate) if candidate else None
        confidence = 0.6 if candidate else 0.2
        value = candidate or (text.splitlines()[0].strip() if text else None)
        return {"value": value, "normalized": normalized, "confidence": confidence}
    except Exception as e:
        logger.exception("Gemini extraction failed: %s", e)
        # final fallback: heuristics on HTML
        candidate = _find_currency_in_text(safe_html)
        if candidate:
            return {"value": candidate, "normalized": _normalize_number(candidate), "confidence": 0.4}
        return {"value": None, "normalized": None, "confidence": 0.0}


def extract_from_image(image_bytes: bytes, description: str):
    """
    If you have a screenshot, send that to Gemini OR (if SDK doesn't support images directly),
    send an OCRed text + prompt. Here we attempt an image-based prompt if SDK supports it.
    Adapt this call to the genai client you have.
    """
    # Try the simplest approach: ask Gemini to extract using an image input + prompt.
    # NOTE: The exact SDK call for multi-modal images depends on your installed SDK version.
    # The fallback is to run OCR (tesseract) locally on screenshot and then call extract_from_text(ocr_text,...).
    try:
        #saving image
        # with open("image.png", "wb") as f:
        #     f.write(image_bytes)
        image_part = genai.types.Part.from_bytes(
            data=image_bytes,
            # The output is PNG, so use the corresponding MIME type
            mime_type='image/png' 
        )
        # example approach (SDKs vary) — adapt to your client:
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[f"Extract the following: {description}.Return value and nothing else.", image_part]
        )
        text = _resp_to_text(resp).strip()
        # m = re.search(r"\{.*\}", text, re.S)
        # if m:
        #     parsed = json.loads(m.group(0))
        #     parsed["normalized"] = parsed.get("normalized") or _normalize_number(parsed.get("value"))
        #     parsed["confidence"] = float(parsed.get("confidence", 0.8))
        #     return {"value": parsed.get("value"), "normalized": parsed.get("normalized"), "confidence": parsed.get("confidence")}
        # # fallback
        print("Extracted text: %s", text)
        return {"value": text}
    except Exception:
        # If image path is unsupported by SDK, you'd use OCR here (e.g., pytesseract) then call extract_from_text()
        return {"value": None}
