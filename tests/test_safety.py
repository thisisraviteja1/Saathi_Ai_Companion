"""
"Attack your own system" tests, automated. Runs the real planner + safety engine against
a Python copy of the sandbox for every demo scenario.

    python tests/test_safety.py        (or: pytest tests/)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import llm  # noqa: E402
import safety  # noqa: E402
from planner import build_pay_plan  # noqa: E402

BILL = {"readable": True, "provider": "Demo Electricity", "consumer_id": "DEMO123",
        "amount": 840.0, "due_date": "2026-10-15", "summary": "x"}
LARGE = {**BILL, "consumer_id": "DEMO456", "amount": 6500.0}
SITE_AMOUNTS = {"DEMO123": 840, "DEMO456": 6500}


class FakeSandbox:
    """Mirrors frontend/sandbox/index.html closely enough to test the rules."""

    def __init__(self, scenario):
        self.scenario = scenario
        self.domain = "electricity-pay-demo.xyz" if scenario == "suspicious" else "sandbox.saathi.local"
        self.page, self.cid = "home", None

    def act(self, step):
        a, t = step["action"], step.get("target")
        if a == "TYPE" and t == "consumer_id":
            self.cid = step["value"]
        elif a == "CLICK" and t == "fetch_bill":
            self.page = "bill"
        elif a == "CLICK" and t == "pay":
            self.page = "otp" if self.scenario == "otp" else "success"
        return self.obs()

    def user_enters_otp(self):
        self.page = "success"

    def obs(self):
        o = {"page": self.page, "domain": self.domain, "fields_requested": []}
        amount = SITE_AMOUNTS.get(self.cid, 0) * (10 if self.scenario == "mismatch" else 1)
        if self.page == "bill":
            o.update(consumer_id=self.cid, amount_due=amount)
        if self.page == "otp":
            o["fields_requested"] = ["otp"]
        if self.page == "success":
            o.update(status="SUCCESS", txn_id="DEMO-1", amount_paid=amount)
        return o


def run(scenario, bill=BILL, approve=True, guardian=None, online=True, lang="en"):
    """Returns the code that ended the run, plus the event trail."""
    task = {"bill": dict(bill), "online": online, "lang": lang,
            "user_confirmed": False, "guardian_approved": False}
    box, events = FakeSandbox(scenario), []
    for step in build_pay_plan(task["bill"], scenario, lang):
        v = safety.check_action(step, task)
        if v["verdict"] == "STOP":
            return v["code"], events
        if v["verdict"] == "CONFIRM":
            if not approve:
                return "USER_DECLINED", events
            task["user_confirmed"] = True
            if v["guardian"]:
                events.append("GUARDIAN_ASKED")
                if not guardian:
                    return "GUARDIAN_DECLINED", events
                task["guardian_approved"] = True
            continue
        obs = box.obs() if step["action"] == "OPEN_PAGE" else box.act(step)
        v = safety.check_observation(obs, task)
        if v["verdict"] == "HANDOFF":
            events.append("HANDOFF")
            box.user_enters_otp()                    # the human types the OTP, not the agent
            v = safety.check_observation(box.obs(), task)
        if v["verdict"] == "STOP":
            return v["code"], events
    return "COMPLETED", events


def test_happy_path():
    assert run("normal")[0] == "COMPLETED"

def test_wrong_amount_stops():
    assert run("mismatch")[0] == "AMOUNT_MISMATCH"

def test_otp_is_handed_to_user_then_completes():
    assert run("otp") == ("COMPLETED", ["HANDOFF"])

def test_suspicious_site_refused():
    assert run("suspicious")[0] == "UNTRUSTED_SITE"

def test_offline_stops_before_acting():
    assert run("normal", online=False)[0] == "OFFLINE"

def test_user_can_decline():
    assert run("normal", approve=False)[0] == "USER_DECLINED"

def test_large_amount_needs_guardian():
    assert run("normal", bill=LARGE, guardian=True) == ("COMPLETED", ["GUARDIAN_ASKED"])

def test_guardian_can_decline():
    assert run("normal", bill=LARGE, guardian=False)[0] == "GUARDIAN_DECLINED"

def test_amount_limit():
    task = {"bill": {**BILL, "amount": 50_000}}
    assert safety.check_action({"action": "CONFIRM", "target": "payment"}, task)["code"] == "AMOUNT_LIMIT"

def test_pay_click_without_confirmation_is_blocked():
    assert safety.check_action({"action": "CLICK", "target": "pay"}, {"bill": BILL})["verdict"] == "STOP"

def test_large_pay_click_without_guardian_is_blocked():
    task = {"bill": LARGE, "user_confirmed": True}
    assert safety.check_action({"action": "CLICK", "target": "pay"}, task)["verdict"] == "STOP"

def test_agent_never_types_secrets():
    for field in ("otp", "pin", "password"):
        v = safety.check_action({"action": "TYPE", "target": field, "value": "1234"}, {"bill": BILL})
        assert v["code"] == "AUTH_HANDOFF"

def test_agent_cannot_type_values_not_on_bill():
    v = safety.check_action({"action": "TYPE", "target": "consumer_id", "value": "OTHER9"}, {"bill": BILL})
    assert v["code"] == "VALUE_NOT_FROM_BILL"

def test_unknown_action_refused():
    assert safety.check_action({"action": "EXECUTE_JS"}, {"bill": BILL})["code"] == "ACTION_NOT_ALLOWED"

def test_messages_are_translated():
    code, _ = run("mismatch", lang="te")
    task = {"bill": BILL, "lang": "hi"}
    v = safety.check_observation({"amount_due": 8400}, task)
    assert "₹8,400" in v["message"] and "सावधान" in v["message"]
    plan = build_pay_plan(BILL, "normal", "te")
    assert all(s["say"] and s["learn"] for s in plan) and "కన్స్యూమర్" in plan[2]["say"]

def test_mock_intent_understands_three_languages():
    assert llm.classify_intent("Saathi, please handle my electricity bill")["intent"] == "PAY_BILL"
    hi = llm.classify_intent("साथी, मेरा बिजली का बिल भर दो")
    assert (hi["intent"], hi["language"]) == ("PAY_BILL", "hi")
    te = llm.classify_intent("సాథీ, నా కరెంట్ బిల్లు కట్టు")
    assert (te["intent"], te["language"]) == ("PAY_BILL", "te")
    assert llm.classify_intent("What does this letter say?")["intent"] == "EXPLAIN_DOCUMENT"
    assert llm.classify_intent("Did my payment go through?")["intent"] == "CHECK_STATUS"

def test_bill_extraction_drops_personal_data():
    cleaned = llm._clean_bill({"consumer_id": "demo123", "amount": "₹ 840.00", "due_date": "2026-10-15",
                               "name": "Lakshmi Devi", "address": "H.No 1-2-3"}, "en")
    assert "name" not in cleaned and "address" not in cleaned
    assert cleaned["amount"] == 840.0 and cleaned["consumer_id"] == "DEMO123" and cleaned["readable"]


if __name__ == "__main__":
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_")]
    for name, fn in tests:
        fn()
        print(f"  ✓ {name}")
    print(f"{len(tests)} passed")
