"""
Tiny persistent store: tasks, the document wallet and guardian requests, saved to
data/saathi.json after every change. Good enough for a hackathon; swap for SQLite later.

Data minimisation: only extracted fields are stored — never the photo.
"""
import json
import os
import random
import time
from pathlib import Path

from planner import TRANSITIONS

DATA = Path(__file__).resolve().parent.parent / "data" / "saathi.json"


class Store:
    def __init__(self, path=DATA):
        self.path = Path(path)
        self.tasks, self.documents = {}, []
        if self.path.exists():
            try:
                d = json.loads(self.path.read_text(encoding="utf-8"))
                self.tasks, self.documents = d.get("tasks", {}), d.get("documents", [])
            except (ValueError, OSError):
                pass

    def save(self):
        self.path.parent.mkdir(exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"tasks": self.tasks, "documents": self.documents},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)

    # ---------------- tasks ----------------
    def create_task(self, intent, bill, scenario="normal", online=True, lang="en"):
        tid = f"T{random.randint(1000, 9999)}"
        while tid in self.tasks:
            tid = f"T{random.randint(1000, 9999)}"
        task = {"id": tid, "intent": intent, "bill": bill, "scenario": scenario, "online": online,
                "lang": lang, "state": "CREATED", "user_confirmed": False, "guardian_approved": False,
                "guardian": None, "plan": [], "history": [], "result": None, "stop": None,
                "created_at": time.time()}
        self.tasks[tid] = task
        self._log(task, "CREATED")
        self.save()
        return task

    def get(self, tid):
        return self.tasks.get(tid)

    def transition(self, task, new_state, note=""):
        if new_state not in TRANSITIONS[task["state"]]:
            raise ValueError(f"illegal transition {task['state']} -> {new_state}")
        task["state"] = new_state
        self._log(task, new_state, note)
        self.save()
        return task

    def stop(self, task, code, message):
        if task["state"] not in ("STOPPED", "COMPLETED"):
            task["stop"] = {"code": code, "message": message}
            self.transition(task, "STOPPED", code)
        return task

    def all_tasks(self):
        return sorted(self.tasks.values(), key=lambda t: -t["created_at"])

    @staticmethod
    def _log(task, state, note=""):
        task["history"].append({"state": state, "note": note, "t": time.time()})

    # ---------------- guardian ----------------
    def pending_guardian(self):
        return [t for t in self.all_tasks() if t["state"] == "WAITING_GUARDIAN"]

    # ---------------- document wallet ----------------
    def save_document(self, kind, fields):
        key = (kind, fields.get("consumer_id"), fields.get("billing_period"), fields.get("title"))
        for d in self.documents:
            if (d["kind"], d.get("consumer_id"), d.get("billing_period"), d.get("title")) == key:
                d.update(fields, saved_at=time.time())
                self.save()
                return d
        doc = {"id": f"D{len(self.documents) + 1:03d}", "kind": kind, **fields, "saved_at": time.time()}
        self.documents.insert(0, doc)
        self.save()
        return doc
