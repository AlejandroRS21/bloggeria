"""Robust JSON extraction from LLM responses.

Different models format JSON differently: some return bare JSON, others wrap it
in ```json ... ``` fences or add prose before/after. Gemini tends to return
clean JSON; Nemotron/DeepSeek often fence it. This helper handles all cases.
"""

import json
import re
from typing import Any


def extract_json(text: str) -> Any:
    """Parse JSON from an LLM response, tolerating fences and surrounding prose.

    Raises json.JSONDecodeError if no valid JSON object/array can be found.
    """
    if text is None:
        raise json.JSONDecodeError("empty response", "", 0)

    s = text.strip()

    # 1) direct parse (clean JSON)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    # 2) fenced code block ```json ... ``` or ``` ... ```
    fence = re.search(r"```(?:json)?\s*(.*?)```", s, re.DOTALL | re.IGNORECASE)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3) first balanced {...} or [...] span
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = s.find(open_ch)
        end = s.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            candidate = s[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise json.JSONDecodeError("no JSON found in response", s[:200], 0)
