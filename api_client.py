"""
api_client.py
Handles calls to the DeepSeek API for PlasticBot.

Important:
- This chatbot is for a PLASTICS-ONLY office recycling bin.
- Bloobin is useful as inspiration for tone and contamination prevention,
  but Bloobin/blue-bin guidance in Singapore is broader than this office bin.
- Therefore, the fallback message must NOT say "all recyclables" or "blue bin".
"""

import json
import os
import urllib.request
import urllib.error


# DeepSeek OpenAI-compatible chat endpoint.
# You can also set these as environment variables instead of hardcoding them.
API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
API_KEY = os.getenv("DEEPSEEK_API_KEY", "PASTE_YOUR_DEEPSEEK_API_KEY_HERE")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


SYSTEM_PROMPT = """
You are PlasticBot, a friendly and precise office recycling assistant for a PLASTICS-ONLY recycling bin.

Core rule:
This bin accepts ONLY eligible plastic items. Do not tell users to place paper, metal, glass, e-waste,
food waste, liquids, tissue, styrofoam, soft toys, textiles, or general waste into this bin.

Always follow this answer structure:
1. Clear verdict: Accepted / Not accepted / Conditional.
2. One short reason.
3. Preparation steps if accepted: empty, clean, dry, flatten if suitable.
4. Redirect if not accepted: use general waste or the correct dedicated recycling stream.
5. If unsure, ask the user for the item material and condition.

Use the provided CSV context as the source of truth.
Do not invent rules not in the data.
Keep answers concise, warm, and practical.
If someone seems to report a bin issue, encourage them to use the report issue form.
"""


def _fallback_response(user_text: str, context: str) -> str:
    """
    Local fallback used when the API URL/key/model is missing or the API call fails.
    This is deliberately plastics-only, not general blue-bin guidance.
    """
    if context:
        return (
            "Based on the matched rule above, follow the plastics-only bin guidance shown. "
            "Before recycling, make sure the item is plastic, empty, clean, and dry. "
            "If it is not plastic or has food/liquid residue, please do not place it in this bin."
        )

    return (
        "I could not find an exact match in the plastics-only rules. Quick check: "
        "only plastic items that are empty, clean, and dry should go into this bin. "
        "If the item is paper, metal, glass, food-stained, liquid-filled, tissue, styrofoam, "
        "e-waste, or general rubbish, please use the correct disposal stream instead."
    )


def call_claude(user_text: str, context: str) -> str:
    """
    Historical function name kept so chatbot.py does not need to change.
    This now calls DeepSeek's OpenAI-compatible API.
    If the API is not configured, it returns a safe plastics-only fallback response.
    """
    if not API_URL.startswith(("http://", "https://")):
        return _fallback_response(user_text, context)

    if not API_KEY or API_KEY == "PASTE_YOUR_DEEPSEEK_API_KEY_HERE":
        return _fallback_response(user_text, context)

    if context:
        user_message = (
            f'User question: "{user_text}"\n\n'
            f"Relevant CSV context:\n{context}\n\n"
            "Answer using the plastics-only rules above."
        )
    else:
        user_message = (
            f'User question: "{user_text}"\n\n'
            "No exact CSV match was found. Give a cautious plastics-only answer. "
            "Do not approve non-plastic items."
        )

    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.2,
        "max_tokens": 500,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        return data["choices"][0]["message"]["content"].strip()

    except (ValueError, KeyError, IndexError, urllib.error.HTTPError,
            urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return _fallback_response(user_text, context)
