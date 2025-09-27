# backend/agents/xpath_agent.py
# Uses Gemini to suggest an XPath for the requested description
from google import genai
from backend.utils.env import GEMINI_API_KEY

# configure genai client
genai_client = genai.Client(api_key=GEMINI_API_KEY)


def ask_gemini_for_xpath(html_snippet: str, description: str) -> str:
    """
    Returns a single XPath string. Truncate HTML to fit token limits.
    """
    safe_html = html_snippet[:3500]  # avoid huge requests
    prompt = (
        "You are an assistant that finds reliable XPaths in HTML. "
        "Given the truncated HTML and a human description of the element to extract, "
        "return the single best XPath expression and nothing else.\n\n"
        f"Description: {description}\n\n"
        f"HTML:\n{safe_html}\n\n"
        "Return only the XPath expression on one line, no explanation."
    )

    resp = genai_client.generate(model="gemini-1.5-pro", prompt=prompt, max_output_tokens=256)
    # resp.output_text or resp.candidates depending on client version
    text = ""
    try:
        text = resp.output[0].content[0].text  # adapt if client returns differently
    except Exception:
        # fallback to available attribute
        text = getattr(resp, "text", "")
    return text.strip()
