"""
One LLM wrapper, three backends, zero extra dependencies (stdlib urllib only).

    LLM_PROVIDER=anthropic   Claude          (ANTHROPIC_API_KEY, LLM_MODEL)
    LLM_PROVIDER=openai      any OpenAI-compatible API: OpenAI, Gemini, Groq, Ollama…
                             (OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL)
    LLM_PROVIDER=mock        no network: keyword rules + synthetic demo documents.
                             The whole app works end-to-end in this mode — your safety
                             net if the wifi dies on stage.

If a real call fails for ANY reason we fall back to mock and mark the result
"source": "fallback" so the UI shows it honestly.
"""
import json
import os
import re
import urllib.request

import i18n
from prompts import (ALLOWED_INTENTS, ALLOWED_SERVICES, BILL_KEYS, EXPLAIN_KEYS,
                     bill_prompt, explain_prompt, intent_prompt)

PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()
MODEL = os.getenv("LLM_MODEL", "")
TIMEOUT = float(os.getenv("LLM_TIMEOUT", "25"))


# ---------------------------------------------------------------------------
# Raw provider calls
# ---------------------------------------------------------------------------
def _post(url, headers, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())


def _call_anthropic(system, text, image_b64=None, media_type="image/png"):
    content = []
    if image_b64:
        content.append({"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}})
    content.append({"type": "text", "text": text})
    data = _post(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
         "content-type": "application/json"},
        {"model": MODEL or "claude-haiku-5-5", "max_tokens": 800, "system": system,
         "messages": [{"role": "user", "content": content}]},
    )
    return "".join(b.get("text", "") for b in data["content"])


def _call_openai(system, text, image_b64=None, media_type="image/png"):
    user = [{"type": "text", "text": text}]
    if image_b64:
        user.append({"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}})
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    data = _post(
        f"{base}/chat/completions",
        {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}", "Content-Type": "application/json"},
        {"model": MODEL or "gpt-4o-mini", "temperature": 0,
         "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
    )
    return data["choices"][0]["message"]["content"]


def _call(system, text, image_b64=None, media_type="image/png"):
    if PROVIDER == "anthropic":
        return _call_anthropic(system, text, image_b64, media_type)
    if PROVIDER == "openai":
        return _call_openai(system, text, image_b64, media_type)
    raise RuntimeError("mock provider")


def _parse_json(raw):
    """LLMs sometimes wrap JSON in ``` fences or add a sentence. Grab the object."""
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"no JSON in LLM output: {raw[:200]}")
    return json.loads(m.group(0))


# ---------------------------------------------------------------------------
# Mock / fallback logic (deterministic)
# ---------------------------------------------------------------------------
_PAY = ["pay", "handle", "settle", "clear", "bhar", "bharo", "bhugtan", "kattu", "kattandi", "chellinchu",
        "jama", "भर", "भुगतान", "चुका", "जमा", "కట్టు", "కట్టండి", "చెల్లించు", "చెల్లించండి", "కట్టేయ్"]
_EXPLAIN = ["letter", "notice", "paper", "form", "explain", "chitti", "patra", "पत्र", "चिट्ठी", "काग़ज़",
            "कागज", "నోటీసు", "ఉత్తరం", "లేఖ", "కాగితం", "వివరించు"]
_READ = ["what", "read", "how much", "kitna", "kya", "enta", "entha", "kitne", "कितना", "क्या", "पढ़",
         "ఎంత", "ఏముంది", "చదువు", "చదివి"]
_STATUS = ["status", "done", "did it", "went through", "go through", "gone through", "successful", "did my", "ho gaya", "hua", "ayyinda", "हो गया", "हुआ",
           "అయ్యిందా", "అయిందా", "పూర్తయిందా"]


def detect_lang(text, default="en"):
    if re.search(r"[ऀ-ॿ]", text):
        return "hi"
    if re.search(r"[ఀ-౿]", text):
        return "te"
    t = text.lower()
    if re.search(r"\b(kya|kitna|bharo|karo|hai|mera|meri|bijli)\b", t):
        return "hi"
    if re.search(r"\b(enta|entha|cheyyi|kattu|undi|naa|karent)\b", t):
        return "te"
    return "en" if t.strip() else i18n.norm(default)


def _mock_intent(text, ui_lang="en"):
    t = text.lower()
    lang = detect_lang(text, ui_lang)
    service = "WATER" if re.search(r"water|paani|pani|neellu|पानी|నీళ్ళ|నీటి", t) else "ELECTRICITY"
    if any(w in t for w in _STATUS):
        intent, key = "CHECK_STATUS", "REPLY_STATUS"
    elif any(w in t for w in _EXPLAIN):
        intent, key = "EXPLAIN_DOCUMENT", "REPLY_EXPLAIN"
    elif any(w in t for w in _PAY):
        intent, key = "PAY_BILL", "REPLY_PAY"
    elif any(w in t for w in _READ) or re.search(r"bill|बिल|బిల్లు", t):
        intent, key = "READ_BILL", "REPLY_READ"
    else:
        intent, key = "UNKNOWN", "REPLY_UNKNOWN"
    return {"intent": intent, "service": service,
            "needs_document": intent in ("PAY_BILL", "READ_BILL", "EXPLAIN_DOCUMENT"),
            "language": lang, "reply": i18n.t(key, lang)}


# Synthetic documents that match the images in assets/ (mock mode can't really see)
DEMO_BILLS = {
    "normal": {"provider": "Demo Electricity", "consumer_id": "DEMO123", "amount": 840.0,
               "due_date": "2026-10-15", "billing_period": "Sep 2026", "units_consumed": 210},
    "large": {"provider": "Demo Electricity", "consumer_id": "DEMO456", "amount": 6500.0,
              "due_date": "2026-10-20", "billing_period": "Sep 2026", "units_consumed": 1420},
}


def _mock_bill(lang, hint):
    b = dict(DEMO_BILLS["large" if hint == "large" else "normal"])
    return {"readable": True, **b, "summary": _summary(b, lang)}


def _summary(b, lang):
    return i18n.t("BILL_SUMMARY", lang, amount=i18n.rupees(b["amount"]), due=i18n.fmt_date(b["due_date"], lang))


# ---------------------------------------------------------------------------
# Validation: never trust LLM output blindly
# ---------------------------------------------------------------------------
def _clean_intent(d, ui_lang):
    out = _mock_intent("", ui_lang)
    out.update({k: d[k] for k in out if k in d})
    if out["intent"] not in ALLOWED_INTENTS:
        out["intent"] = "UNKNOWN"
    if out["service"] not in ALLOWED_SERVICES:
        out["service"] = "UNKNOWN"
    out["language"] = i18n.norm(out["language"])
    out["reply"] = str(out["reply"])[:200]
    return out


def _clean_bill(d, lang):
    out = {k: d.get(k) for k in BILL_KEYS}  # drop extra keys = data minimisation
    try:
        out["amount"] = float(str(out["amount"]).replace(",", "").replace("₹", "").strip()) \
            if out["amount"] not in (None, "") else None
    except ValueError:
        out["amount"] = None
    if out["consumer_id"]:
        out["consumer_id"] = str(out["consumer_id"]).strip().upper()
    required = ("consumer_id", "amount", "due_date")
    out["readable"] = bool(d.get("readable", True)) and all(out[k] not in (None, "") for k in required)
    if out["readable"]:
        out["summary"] = out["summary"] or _summary(out, lang)
    return out


def _clean_explain(d):
    out = {k: d.get(k) for k in EXPLAIN_KEYS}
    out["actions"] = [str(a) for a in (out["actions"] or [])][:4]
    out["readable"] = bool(d.get("readable", True)) and bool(out["explanation"])
    return out


def _unreadable(keys, lang, source):
    return {**{k: None for k in keys}, "readable": False, "summary": i18n.t("UNREADABLE", lang), "source": source}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def classify_intent(text, ui_lang="en"):
    if PROVIDER != "mock":
        try:
            return {**_clean_intent(_parse_json(_call(intent_prompt(ui_lang), text)), ui_lang), "source": "llm"}
        except Exception as e:  # noqa: BLE001
            print(f"[llm] intent fallback: {e}")
            return {**_mock_intent(text, ui_lang), "source": "fallback"}
    return {**_mock_intent(text, ui_lang), "source": "mock"}


def extract_bill(image_b64, media_type="image/png", lang="en", hint=None):
    lang = i18n.norm(lang)
    if PROVIDER != "mock" and image_b64:
        try:
            raw = _call(bill_prompt(lang), "Read this bill.", image_b64, media_type)
            bill = _clean_bill(_parse_json(raw), lang)
            if not bill["readable"]:
                return _unreadable(BILL_KEYS, lang, "llm")
            return {**bill, "source": "llm"}
        except Exception as e:  # noqa: BLE001
            print(f"[llm] bill fallback: {e}")
            source = "fallback"
    else:
        source = "mock"
    if hint == "unreadable":          # mock can't see blur; the demo scenario tells it
        return _unreadable(BILL_KEYS, lang, source)
    return {**_mock_bill(lang, hint), "source": source}


def explain_document(image_b64, media_type="image/png", lang="en", hint=None):
    lang = i18n.norm(lang)
    if PROVIDER != "mock" and image_b64:
        try:
            out = _clean_explain(_parse_json(_call(explain_prompt(lang), "Explain this document.", image_b64, media_type)))
            if not out["readable"]:
                return _unreadable(EXPLAIN_KEYS, lang, "llm")
            return {**out, "source": "llm"}
        except Exception as e:  # noqa: BLE001
            print(f"[llm] explain fallback: {e}")
            source = "fallback"
    else:
        source = "mock"
    if hint == "unreadable":
        return _unreadable(EXPLAIN_KEYS, lang, source)
    return {"readable": True, "doc_type": "letter", "deadline": "2026-11-30", **i18n.DEMO_LETTER[lang], "source": source}
