"""
Saathi backend.   ./run.sh   (or: python backend/main.py)   → http://localhost:8000

API (the frozen contract — see README):
  GET  /api/health
  POST /api/intent               {text, lang}                          -> intent
  POST /api/read-bill            {image_b64, media_type, lang, demo_hint} -> bill (+ saved to wallet)
  POST /api/explain              {image_b64, media_type, lang, demo_hint} -> explanation (+ wallet)
  GET  /api/documents                                                  -> document wallet
  POST /api/tasks                {intent, bill, scenario, online, lang} -> task (+ plan)
  GET  /api/tasks  |  GET /api/tasks/{id}
  GET  /api/status?lang=xx                                             -> spoken status of last task
  POST /api/tasks/{id}/check-step {step}                               -> safety verdict (BEFORE)
  POST /api/tasks/{id}/observe    {step, observation}                  -> safety verdict (AFTER)
  POST /api/tasks/{id}/confirm    {approved, ask_guardian}             -> task
  POST /api/tasks/{id}/cancel                                          -> task
  POST /api/tasks/{id}/finish                                          -> task (READ_BILL flow)
  GET  /api/guardian/requests                                          -> tasks waiting for family
  POST /api/guardian/{id}         {approved}                           -> task
"""
import os
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

# Load .env without needing python-dotenv
_env = ROOT / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import uvicorn  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse  # noqa: E402
from starlette.routing import Mount, Route  # noqa: E402
from starlette.staticfiles import StaticFiles  # noqa: E402

import i18n  # noqa: E402
import llm  # noqa: E402
import safety  # noqa: E402
from planner import build_pay_plan  # noqa: E402
from store import Store  # noqa: E402

store = Store()
GUARDIAN_NAME = os.getenv("GUARDIAN_NAME", "Ravi (son)")


def err(msg, code=400):
    return JSONResponse({"error": msg}, status_code=code)


async def body(req):
    try:
        return await req.json()
    except ValueError:
        return {}


def _b64(b):
    s = b.get("image_b64") or ""
    return s.split(",", 1)[1] if s.startswith("data:") else s


# ------------------------------------------------------------------ understanding
async def health(_):
    return JSONResponse({"ok": True, "llm_provider": llm.PROVIDER, "model": llm.MODEL or "default",
                         "guardian_threshold": safety.GUARDIAN_THRESHOLD, "max_amount": safety.MAX_AMOUNT})


async def intent(req: Request):
    b = await body(req)
    text = (b.get("text") or "").strip()
    if not text:
        return err("text is required")
    return JSONResponse(llm.classify_intent(text, i18n.norm(b.get("lang"))))


async def read_bill(req: Request):
    b = await body(req)
    bill = llm.extract_bill(_b64(b), b.get("media_type", "image/png"), b.get("lang"), b.get("demo_hint"))
    if bill["readable"]:
        store.save_document("bill", {k: bill[k] for k in ("provider", "consumer_id", "amount", "due_date",
                                                           "billing_period", "units_consumed")})
    return JSONResponse(bill)


async def explain(req: Request):
    b = await body(req)
    out = llm.explain_document(_b64(b), b.get("media_type", "image/png"), b.get("lang"), b.get("demo_hint"))
    if out["readable"]:
        store.save_document("letter", {k: out[k] for k in ("doc_type", "title", "explanation", "actions", "deadline")})
    return JSONResponse(out)


async def documents(_):
    return JSONResponse(store.documents)


# ------------------------------------------------------------------ tasks
def _task(req):
    return store.get(req.path_params["tid"])


async def create_task(req: Request):
    b = await body(req)
    bill = b.get("bill") or {}
    if not bill.get("readable"):
        return err("bill is not readable")
    lang = i18n.norm(b.get("lang"))
    task = store.create_task(b.get("intent", "PAY_BILL"), bill, b.get("scenario", "normal"),
                             bool(b.get("online", True)), lang)
    store.transition(task, "READ", bill.get("summary", ""))
    if task["intent"] == "PAY_BILL":
        task["plan"] = build_pay_plan(bill, task["scenario"], lang)
        store.transition(task, "PLANNED", f"{len(task['plan'])} steps")
    return JSONResponse(task)


async def list_tasks(_):
    return JSONResponse([{k: t[k] for k in ("id", "intent", "state", "bill", "result", "stop", "created_at")}
                         for t in store.all_tasks()])


async def get_task(req: Request):
    task = _task(req)
    return JSONResponse(task) if task else err("no such task", 404)


async def status(req: Request):
    lang = i18n.norm(req.query_params.get("lang"))
    tasks = store.all_tasks()
    if not tasks:
        return JSONResponse({"message": i18n.t("STATUS_NONE", lang), "task": None})
    t = tasks[0]
    amount = i18n.rupees(t["bill"].get("amount"))
    if t["state"] == "COMPLETED" and t["result"]:
        msg = i18n.t("STATUS_DONE", lang, amount=amount, txn=t["result"]["txn_id"])
    elif t["state"] == "COMPLETED":
        msg = i18n.t("STATUS_EXPLAINED", lang, amount=amount)
    elif t["state"] == "STOPPED" and (t["stop"] or {}).get("code") == "VERIFY_FAILED":
        msg = i18n.t("VERIFY_FAILED", lang)
    elif t["state"] == "STOPPED":
        msg = i18n.t("STATUS_STOPPED", lang, reason=(t["stop"] or {}).get("message", ""))
    else:
        msg = i18n.t("STATUS_WAITING", lang)
    return JSONResponse({"message": msg, "task": {k: t[k] for k in ("id", "state", "result")}})


async def check_step(req: Request):
    task = _task(req)
    if not task:
        return err("no such task", 404)
    if task["state"] in ("STOPPED", "COMPLETED"):
        return err(f"task is {task['state']}")
    step = (await body(req)).get("step", {})
    verdict = safety.check_action(step, task)
    if task["state"] == "PLANNED":
        store.transition(task, "RUNNING")
    if verdict["verdict"] == "CONFIRM":
        store.transition(task, "WAITING_CONFIRMATION", verdict["message"])
    elif verdict["verdict"] == "STOP":
        store.stop(task, verdict["code"], verdict["message"])
    return JSONResponse({**verdict, "task_state": task["state"]})


async def observe(req: Request):
    task = _task(req)
    if not task:
        return err("no such task", 404)
    if task["state"] in ("STOPPED", "COMPLETED"):
        return err(f"task is {task['state']}")
    b = await body(req)
    step, obs = b.get("step", {}), b.get("observation", {})
    verdict = safety.check_observation(obs, task)

    if verdict["verdict"] == "STOP":
        store.stop(task, verdict["code"], verdict["message"])
        return JSONResponse({**verdict, "task_state": task["state"]})
    if verdict["verdict"] == "HANDOFF":
        if task["state"] == "RUNNING":
            store.transition(task, "WAITING_USER", verdict["field"])
        return JSONResponse({**verdict, "task_state": task["state"]})
    if task["state"] == "WAITING_USER":
        store.transition(task, "RUNNING", "user finished the private step")

    # Advance the state machine on the steps that matter
    if step.get("action") == "CLICK" and step.get("target") == "pay" and task["state"] == "RUNNING":
        store.transition(task, "EXECUTED", obs.get("txn_id", ""))
    if step.get("target") == "result" and task["state"] == "EXECUTED":
        paid = obs.get("amount_paid")
        if obs.get("status") == "SUCCESS" and paid is not None and abs(float(paid) - float(task["bill"]["amount"])) < 0.5:
            store.transition(task, "VERIFIED", obs.get("txn_id", ""))
            task["result"] = {"txn_id": obs.get("txn_id"), "amount": paid, "at": time.time()}
            store.transition(task, "COMPLETED")
        else:
            msg = i18n.t("VERIFY_FAILED", task["lang"])
            store.stop(task, "VERIFY_FAILED", msg)
            return JSONResponse({"verdict": "STOP", "code": "VERIFY_FAILED", "message": msg,
                                 "task_state": task["state"]})
    return JSONResponse({**verdict, "task_state": task["state"]})


async def confirm(req: Request):
    task = _task(req)
    if not task:
        return err("no such task", 404)
    if task["state"] != "WAITING_CONFIRMATION":
        return err("task is not waiting for confirmation")
    b = await body(req)
    if not b.get("approved"):
        store.stop(task, "USER_DECLINED", i18n.t("USER_DECLINED", task["lang"]))
        return JSONResponse(task)
    task["user_confirmed"] = True
    needs_guardian = float(task["bill"]["amount"]) > safety.GUARDIAN_THRESHOLD or bool(b.get("ask_guardian"))
    if needs_guardian and not task["guardian_approved"]:
        task["guardian"] = {"name": GUARDIAN_NAME, "status": "pending", "requested_at": time.time()}
        store.transition(task, "WAITING_GUARDIAN", GUARDIAN_NAME)
    else:
        store.transition(task, "RUNNING", "user approved")
    return JSONResponse(task)


async def cancel(req: Request):
    task = _task(req)
    if not task:
        return err("no such task", 404)
    store.stop(task, "USER_CANCELLED", i18n.t("USER_CANCELLED", task["lang"]))
    return JSONResponse(task)


async def finish(req: Request):
    task = _task(req)
    if not task:
        return err("no such task", 404)
    if task["state"] == "READ":
        store.transition(task, "COMPLETED", "explained to user")
    return JSONResponse(task)


# ------------------------------------------------------------------ guardian
async def guardian_requests(_):
    return JSONResponse([{"id": t["id"], "amount": t["bill"]["amount"], "provider": t["bill"].get("provider"),
                          "consumer_id": t["bill"].get("consumer_id"), "due_date": t["bill"].get("due_date"),
                          "guardian": t["guardian"]} for t in store.pending_guardian()])


async def guardian_decide(req: Request):
    task = _task(req)
    if not task:
        return err("no such task", 404)
    if task["state"] != "WAITING_GUARDIAN":
        return err("task is not waiting for a guardian")
    approved = bool((await body(req)).get("approved"))
    task["guardian"]["status"] = "approved" if approved else "declined"
    task["guardian"]["decided_at"] = time.time()
    if approved:
        task["guardian_approved"] = True
        store.transition(task, "RUNNING", "guardian approved")
    else:
        store.stop(task, "GUARDIAN_DECLINED", i18n.t("GUARDIAN_DECLINED", task["lang"]))
    return JSONResponse(task)


app = Starlette(routes=[
    Route("/api/health", health),
    Route("/api/intent", intent, methods=["POST"]),
    Route("/api/read-bill", read_bill, methods=["POST"]),
    Route("/api/explain", explain, methods=["POST"]),
    Route("/api/documents", documents),
    Route("/api/status", status),
    Route("/api/tasks", create_task, methods=["POST"]),
    Route("/api/tasks", list_tasks, methods=["GET"]),
    Route("/api/tasks/{tid}", get_task),
    Route("/api/tasks/{tid}/check-step", check_step, methods=["POST"]),
    Route("/api/tasks/{tid}/observe", observe, methods=["POST"]),
    Route("/api/tasks/{tid}/confirm", confirm, methods=["POST"]),
    Route("/api/tasks/{tid}/cancel", cancel, methods=["POST"]),
    Route("/api/tasks/{tid}/finish", finish, methods=["POST"]),
    Route("/api/guardian/requests", guardian_requests),
    Route("/api/guardian/{tid}", guardian_decide, methods=["POST"]),
    Mount("/assets", StaticFiles(directory=ROOT / "assets")),
    Mount("/", StaticFiles(directory=ROOT / "frontend", html=True)),
])


def _lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    ip = _lan_ip()
    print("\n  Saathi is running")
    print(f"  App:            http://localhost:{port}")
    print(f"  Family approval: http://localhost:{port}/guardian.html")
    if ip:
        print(f"  On a phone (same wifi): http://{ip}:{port}/guardian.html")
    print(f"  AI provider:    {llm.PROVIDER}\n  Press Ctrl+C to stop.\n")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
