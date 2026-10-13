"""
Saathi Safety Engine — deterministic. No LLM is involved in any decision here.

Every agent step is checked TWICE:
  1. before it runs  -> check_action(step, task)       is this action allowed?
  2. after it runs   -> check_observation(obs, task)   is what we now see safe?

Verdicts:
  ALLOW    agent continues
  CONFIRM  pause, show the user exactly what will happen, wait for YES
           (+ "guardian": True  -> a family member must also approve)
  HANDOFF  a private step (OTP/PIN/password…) — the USER does it, Saathi waits, then verifies
  STOP     agent stops and hands control back to the user

This is the slide to show judges: the LLM never decides whether money moves.
"""
import i18n
from i18n import rupees, t

ALLOWED_ACTIONS = {"OPEN_PAGE", "CLICK", "TYPE", "READ", "CONFIRM", "STOP"}
TRUSTED_DOMAINS = {"sandbox.saathi.local"}
HANDOFF_FIELDS = {"otp", "pin", "password", "captcha", "biometric"}
HIGH_RISK_TARGETS = {"pay", "pay_now", "submit_payment", "transfer", "confirm_payment"}

GUARDIAN_THRESHOLD = 5_000   # above this, a family member must also approve
MAX_AMOUNT = 10_000          # above this, Saathi refuses outright


def _v(verdict, code, message="", **extra):
    return {"verdict": verdict, "code": code, "message": message, **extra}


def check_action(step, task):
    """Called BEFORE the agent executes `step`."""
    lang = task.get("lang", "en")
    action = step.get("action")
    target = (step.get("target") or "").lower()
    bill = task["bill"]

    if not task.get("online", True) and action in ("OPEN_PAGE", "CLICK", "TYPE"):
        return _v("STOP", "OFFLINE", t("OFFLINE", lang))

    if action not in ALLOWED_ACTIONS:
        return _v("STOP", "ACTION_NOT_ALLOWED", t("ACTION_NOT_ALLOWED", lang))

    if action == "TYPE" and target in HANDOFF_FIELDS:   # the agent itself never types secrets
        return _v("STOP", "AUTH_HANDOFF", t("AUTH_HANDOFF", lang, thing=i18n.thing(target, lang)))

    if action == "TYPE" and target == "consumer_id" and str(step.get("value")) != str(bill.get("consumer_id")):
        return _v("STOP", "VALUE_NOT_FROM_BILL", t("VALUE_NOT_FROM_BILL", lang))

    if action == "CONFIRM":
        amount = float(bill.get("amount") or 0)
        if amount > MAX_AMOUNT:
            return _v("STOP", "AMOUNT_LIMIT", t("AMOUNT_LIMIT", lang, amount=rupees(amount)))
        msg = t("PAYMENT_APPROVAL", lang, amount=rupees(amount), provider=bill.get("provider") or "")
        guardian = amount > GUARDIAN_THRESHOLD
        if guardian:
            msg += " " + t("GUARDIAN_NEEDED", lang)
        return _v("CONFIRM", "PAYMENT_APPROVAL", msg, amount=amount, guardian=guardian)

    if action == "CLICK" and target in HIGH_RISK_TARGETS:
        if not task.get("user_confirmed"):
            return _v("STOP", "NO_CONFIRMATION", t("NO_CONFIRMATION", lang))
        if float(bill.get("amount") or 0) > GUARDIAN_THRESHOLD and not task.get("guardian_approved"):
            return _v("STOP", "NO_CONFIRMATION", t("NO_CONFIRMATION", lang))

    return _v("ALLOW", "OK")


def check_observation(obs, task):
    """Called AFTER each step with what the agent now sees on the service."""
    lang = task.get("lang", "en")
    bill = task["bill"]

    domain = obs.get("domain")
    if domain and domain not in TRUSTED_DOMAINS:
        return _v("STOP", "UNTRUSTED_SITE", t("UNTRUSTED_SITE", lang, domain=domain), domain=domain)

    for f in obs.get("fields_requested", []):
        if f.lower() in HANDOFF_FIELDS:
            return _v("HANDOFF", "AUTH_HANDOFF", t("AUTH_HANDOFF", lang, thing=i18n.thing(f.lower(), lang)),
                      field=f.lower())

    seen, expected = obs.get("amount_due"), bill.get("amount")
    if seen is not None and expected is not None and abs(float(seen) - float(expected)) > 0.5:
        return _v("STOP", "AMOUNT_MISMATCH",
                  t("AMOUNT_MISMATCH", lang, bill=rupees(expected), site=rupees(seen)),
                  bill_amount=expected, site_amount=seen)

    seen_id = obs.get("consumer_id")
    if seen_id and seen_id != bill.get("consumer_id"):
        return _v("STOP", "ACCOUNT_MISMATCH", t("ACCOUNT_MISMATCH", lang))

    return _v("ALLOW", "OK")
