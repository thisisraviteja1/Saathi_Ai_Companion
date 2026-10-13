// Saathi frontend — plain JS, no build step.
// Sections: helpers · stage panels · voice · screens · Saathi's eyes · understanding · agent runner
//           · confirm / family / handoff · learn + practice · tasks + wallet · tricks + autopilot · intro · boot
"use strict";

const $ = (id) => document.getElementById(id);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const SPEECH = { en: "en-IN", hi: "hi-IN", te: "te-IN" };
const MAIN_STATES = ["CREATED", "READ", "PLANNED", "RUNNING", "WAITING_CONFIRMATION", "EXECUTED", "VERIFIED", "COMPLETED"];
const STATE_NAMES = {
  CREATED: "Asked", READ: "Read", PLANNED: "Planned", RUNNING: "Working", WAITING_CONFIRMATION: "Her approval",
  WAITING_GUARDIAN: "Family approval", WAITING_USER: "Her OTP", EXECUTED: "Paid", VERIFIED: "Verified",
  COMPLETED: "Done", STOPPED: "Stopped",
};

const ctx = { intent: null, bill: null, task: null, mode: "bill", sample: null, cancelled: false, lastState: "CREATED",
              stats: null, trick: null, approvals: 0 };

// ------------------------------------------------------------------ helpers
async function api(path, body) {
  let res;
  try {
    res = await fetch("/api" + path, body === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
  } catch (e) {
    showBanner("server");
    throw e;
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

const rupees = (n) => (n == null ? "₹—" : "₹" + Number(n).toLocaleString("en-IN", { maximumFractionDigits: 2 }));
function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso + "T00:00:00");
  return isNaN(d) ? iso : d.toLocaleDateString(LANG + "-IN", { day: "numeric", month: "long", year: "numeric" });
}
const fmtTime = (ts) => new Date(ts * 1000).toLocaleString(LANG + "-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });
const scenario = () => $("scenario").value;
const online = () => navigator.onLine && !$("offline").checked;
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function showBanner(kind) {
  const b = $("banner");
  b.hidden = false;
  b.innerHTML = kind === "file"
    ? "Open Saathi through its server: in the saathi folder run <code>bash run.sh</code> (Mac) or <code>run.bat</code> (Windows), then go to <code>http://localhost:8000</code>."
    : "Saathi's server isn't reachable. Keep the Terminal window running <code>bash run.sh</code> open, then reload this page.";
}

// ------------------------------------------------------------------ stage panels (judge view)
const RULES = {
  OK: "", PAYMENT_APPROVAL: "rule: human approves every payment", AMOUNT_MISMATCH: "rule: amount must match the paper bill",
  UNTRUSTED_SITE: "rule: trusted services only", AUTH_HANDOFF: "rule: Saathi never types OTP, PIN or password",
  OFFLINE: "rule: no payment without a connection", AMOUNT_LIMIT: "rule: ₹10,000 limit",
  VALUE_NOT_FROM_BILL: "rule: type only what's on the bill", NO_CONFIRMATION: "rule: no pay click without approval",
  ACCOUNT_MISMATCH: "rule: account must match the bill", VERIFY_FAILED: "rule: receipt must match the bill",
  USER_DECLINED: "she said no", USER_CANCELLED: "she cancelled", GUARDIAN_DECLINED: "family said no",
};

function log(verdict, text, code = "") {
  const li = document.createElement("li");
  li.className = verdict;
  const rule = RULES[code] || "";
  li.innerHTML = `<span class="v">${verdict}</span><span class="t">${esc(text)}${rule ? `<small>${esc(rule)}</small>` : ""}</span>`;
  $("log").querySelector(".idle")?.remove();
  $("log").prepend(li);
}

function resetLog() {
  $("log").innerHTML = `<li class="idle">Every step is checked before it runs and after it runs.</li>`;
}

function renderStates(current, stopped = false) {
  const list = [...MAIN_STATES];
  if (current === "WAITING_GUARDIAN") list.splice(list.indexOf("WAITING_CONFIRMATION") + 1, 0, "WAITING_GUARDIAN");
  if (current === "WAITING_USER") list.splice(list.indexOf("EXECUTED"), 0, "WAITING_USER");
  const idx = list.indexOf(current);
  $("states").innerHTML = list.map((s, i) => {
    const cls = [i === idx ? (stopped ? "bad" : "on") : i < idx ? "past" : "",
                 s === "WAITING_GUARDIAN" || s === "WAITING_USER" ? "side" : ""].join(" ");
    const name = stopped && i === idx ? `Stopped at: ${STATE_NAMES[s]}` : STATE_NAMES[s];
    return `<li class="${cls}" title="${s}"><i></i><span>${name}</span></li>`;
  }).join("");
}

function setState(s) {
  if (!s) return;
  if (ctx.task) ctx.task.state = s;
  if (s === "STOPPED") return renderStates(ctx.lastState, true);
  ctx.lastState = s;
  renderStates(s);
}

const check = () => { if (ctx.stats) ctx.stats.checks++; };

function renderKnows(kind, data) {
  const rows = kind === "bill"
    ? [["Amount", rupees(data.amount)], ["Due date", data.due_date], ["Consumer ID", data.consumer_id],
       ["Provider", data.provider], ["Bill month", data.billing_period]]
    : [["About", data.title], ["Deadline", data.deadline || "none"], ["Steps to take", (data.actions || []).length]];
  const never = kind === "bill" ? ["Her name", "Her address", "The photo"] : ["Her name", "PPO number", "Her address", "The photo"];
  $("knows-body").innerHTML = `
    <dl class="kept">${rows.map(([k, v]) => `<dt class="k">${k}</dt><dd class="val" style="margin:0">${esc(v ?? "—")}</dd>`).join("")}</dl>
    <h3>Seen on the photo, never stored</h3>
    <ul class="dropped">${never.map((n) => `<li>${n}</li>`).join("")}</ul>`;
}

function renderProof(amount) {
  const s = ctx.stats;
  const secs = Math.max(1, Math.round((Date.now() - s.start) / 1000));
  $("knows-body").insertAdjacentHTML("afterbegin", `
    <div class="proof">
      <div class="hl"><b>${secs}s</b><span>from request to verified payment</span></div>
      <div><b>${s.checks}</b><span>safety checks passed</span></div>
      <div><b>0</b><span>passwords or OTPs typed by Saathi</span></div>
      <div><b>${ctx.approvals}</b><span>human ${ctx.approvals === 1 ? "approval" : "approvals"} before ${rupees(amount)} moved</span></div>
    </div>`);
}

// ------------------------------------------------------------------ voice
// Web Speech API (Chrome / Edge). The text box and buttons always work as a fallback.
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let voices = [];
let currentRec = null;
let meter = null;
const loadVoices = () => (voices = window.speechSynthesis ? speechSynthesis.getVoices() : []);

function voiceFor(lang) {
  const code = SPEECH[lang];
  return voices.find((v) => v.lang === code) || voices.find((v) => v.lang.replace("_", "-").startsWith(lang + "-")) || null;
}

function speak(text, lang = LANG) {
  if ($("mute").checked || !window.speechSynthesis || !text) return Promise.resolve();
  speechSynthesis.cancel();
  const v = voiceFor(lang);
  if (!v && lang !== "en") return Promise.resolve();   // no voice for this language on this computer: text only
  return new Promise((resolve) => {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = SPEECH[lang] || "en-IN";
    if (v) u.voice = v;
    u.rate = 0.92;                                       // a little slower for elderly listeners
    const done = () => { document.body.classList.remove("speaking"); resolve(); };
    u.onend = u.onerror = done;
    document.body.classList.add("speaking");
    speechSynthesis.speak(u);
    setTimeout(done, Math.min(20000, 2500 + text.length * 90));   // never hang the flow on TTS
  });
}

// Live mic level drives the orb (best effort — speech recognition works without it)
async function startMeter() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ac = new (window.AudioContext || window.webkitAudioContext)();
    const an = ac.createAnalyser();
    an.fftSize = 512;
    ac.createMediaStreamSource(stream).connect(an);
    const buf = new Uint8Array(an.fftSize);
    let raf;
    const tick = () => {
      an.getByteTimeDomainData(buf);
      let sum = 0;
      for (const x of buf) sum += (x - 128) ** 2;
      $("mic").style.setProperty("--level", Math.min(1, Math.sqrt(sum / buf.length) / 30).toFixed(3));
      raf = requestAnimationFrame(tick);
    };
    tick();
    meter = () => { cancelAnimationFrame(raf); stream.getTracks().forEach((t) => t.stop()); ac.close(); $("mic").style.setProperty("--level", 0); };
  } catch { meter = null; }
}
const stopMeter = () => { meter?.(); meter = null; };

function listenOnce(onInterim) {
  return new Promise((resolve, reject) => {
    if (!SR) return reject(new Error(tr("mic_unsupported")));
    const rec = new SR();
    currentRec = rec;
    rec.lang = SPEECH[LANG]; rec.interimResults = true; rec.maxAlternatives = 1;
    let final = "", last = "";
    rec.onresult = (e) => {
      last = Array.from(e.results).map((r) => r[0].transcript).join(" ");
      onInterim && onInterim(last);
      if (e.results[e.results.length - 1].isFinal) final = last;
    };
    rec.onerror = (e) => reject(new Error(e.error === "not-allowed" ? "Please allow the microphone in Chrome." : e.error));
    rec.onend = () => { currentRec = null; resolve((final || last).trim()); };
    rec.start();
  });
}
const stopListening = () => { try { currentRec?.abort(); } catch { /* ignore */ } };

// ------------------------------------------------------------------ screens
const screenWaiters = [];
function show(id) {
  document.querySelectorAll(".screen").forEach((s) => s.classList.toggle("active", s.id === "s-" + id));
  $("s-" + id).closest(".companion").scrollTop = 0;
  screenWaiters.splice(0).forEach((w) => (w.ids.includes(id) ? w.resolve(id) : screenWaiters.push(w)));
}
const currentScreen = () => document.querySelector(".screen.active")?.id.slice(2);
function waitFor(ids, timeout = 15000) {
  if (ids.includes(currentScreen())) return Promise.resolve(currentScreen());
  return new Promise((resolve) => {
    const w = { ids, resolve };
    screenWaiters.push(w);
    setTimeout(() => { const i = screenWaiters.indexOf(w); if (i >= 0) { screenWaiters.splice(i, 1); resolve(null); } }, timeout);
  });
}

const STOP_UI = {
  AUTH_HANDOFF: ["🔐", "your_turn"], UNTRUSTED_SITE: ["⚠️", "cant_trust"], OFFLINE: ["📶", "no_internet"],
  UNREADABLE: ["📷", "couldnt_read"], USER_DECLINED: ["✋", "payment_cancelled"], USER_CANCELLED: ["✋", "payment_cancelled"],
  NO_CONFIRMATION: ["✋", "payment_cancelled"], GUARDIAN_DECLINED: ["👨‍👩‍👦", "payment_cancelled"], AMOUNT_MISMATCH: ["", "stopped"],
};

function stop(v) {
  stopListening();
  const [icon, title] = STOP_UI[v.code] || ["🚨", "stopped"];
  $("stop-icon").textContent = icon;
  $("stop-title").textContent = tr(title);
  $("stop-msg").textContent = v.message || tr("something_wrong");
  $("stop-code").textContent = "safety rule: " + v.code;

  // Side-by-side proof of the trick Saathi caught
  const cmp = $("compare");
  cmp.hidden = true;
  cmp.classList.remove("domains");
  if (v.code === "AMOUNT_MISMATCH" && v.site_amount != null) {
    $("cmp-a-label").textContent = tr("cmp_bill"); $("cmp-a").textContent = rupees(v.bill_amount);
    $("cmp-b-label").textContent = tr("cmp_site"); $("cmp-b").textContent = rupees(v.site_amount);
    cmp.hidden = false;
  } else if (v.code === "UNTRUSTED_SITE" && v.domain) {
    $("cmp-a-label").textContent = tr("cmp_trusted"); $("cmp-a").textContent = "sandbox.saathi.local";
    $("cmp-b-label").textContent = tr("cmp_seen"); $("cmp-b").textContent = v.domain;
    cmp.classList.add("domains");
    cmp.hidden = false;
  }
  const shield = document.querySelector("#s-stopped .shield");
  shield.classList.remove("shake");
  if (!["USER_DECLINED", "USER_CANCELLED", "GUARDIAN_DECLINED"].includes(v.code)) requestAnimationFrame(() => shield.classList.add("shake"));

  if (ctx.task) setState("STOPPED");
  show("stopped");
  speak(v.message);
  markTrick(v.code);
}

function setLang(lang, persist = true) {
  applyLang(lang);
  $("lang").value = LANG;
  document.querySelectorAll("[data-sample]").forEach((b) => (b.textContent = "“" + tr(b.dataset.sample) + "”"));
  $("doc-say").textContent = tr(ctx.mode === "letter" ? "show_paper" : "show_bill");
  if (persist) try { localStorage.setItem("saathi-lang", LANG); } catch { /* storage blocked */ }
}

// ------------------------------------------------------------------ Saathi's eyes
// Where the fields sit on the sample documents (percent of the image). Real photos get the scan
// animation only — the AI reads them, we just don't know the coordinates.
const BILL_BOXES = {
  keep: [
    { k: "provider", l: 3.4, t: 2.4, w: 57.2, h: 5.0 },
    { k: "consumer_id", l: 39, t: 25, w: 16.6, h: 3.5, side: true },
    { k: "amount", l: 6.8, t: 68.2, w: 34.7, h: 6.3, wl: 41.9 },
    { k: "due", l: 59, t: 69, w: 29.2, h: 4.2 },
  ],
  hide: [{ l: 39, t: 20.6, w: 44.1, h: 3.9 }, { l: 39, t: 29.4, w: 60, h: 3.9 }],
};
const LETTER_BOXES = {
  keep: [
    { k: "about", l: 3.4, t: 2.9, w: 93.8, h: 3.6 },
    { k: "subject", l: 3.4, t: 29.9, w: 71, h: 3.9 },
    { k: "deadline", l: 3.4, t: 50.2, w: 24.5, h: 4.0 },
  ],
  hide: [{ l: 3.3, t: 19.3, w: 37, h: 7.9 }],
};
const BOX_LABEL = { provider: "provider", consumer_id: "consumer_id", amount: "amount", due: "due", about: "provider", subject: "", deadline: "deadline" };

async function eyesReveal() {
  const layer = $("eyes-layer");
  const map = ctx.sample === "letter" ? LETTER_BOXES : ctx.sample === "bill" || ctx.sample === "large" ? BILL_BOXES : null;
  if (!map || scenario() === "unreadable") return;
  for (const b of map.keep) {
    const w = ctx.sample === "large" && b.wl ? b.wl : b.w;
    layer.insertAdjacentHTML("beforeend",
      `<div class="box${b.side ? " side" : ""}" style="left:${b.l}%;top:${b.t}%;width:${w}%;height:${b.h}%">${BOX_LABEL[b.k] ? `<b>${esc(tr(BOX_LABEL[b.k]))}</b>` : ""}</div>`);
    await sleep(320);
  }
  for (const b of map.hide) {
    layer.insertAdjacentHTML("beforeend",
      `<div class="redact" style="left:${b.l}%;top:${b.t}%;width:${b.w}%;height:${b.h}%"><b>${esc(tr("not_stored"))}</b></div>`);
  }
  await sleep(1300);
}

// ------------------------------------------------------------------ understanding
async function handleRequest(text) {
  if (!text) return;
  $("transcript").textContent = "“" + text + "”";
  let intent;
  try {
    intent = await api("/intent", { text, lang: LANG });
  } catch {
    return speak(tr("something_wrong"));
  }
  ctx.intent = intent;
  ctx.stats = { start: Date.now(), checks: 0 };
  ctx.approvals = 0;
  if (intent.language && intent.language !== LANG) setLang(intent.language);   // answer in the user's language

  if (intent.intent === "CHECK_STATUS") {
    const s = await api(`/status?lang=${LANG}`);
    $("transcript").textContent = s.message;
    return speak(s.message);
  }
  if (intent.intent === "UNKNOWN") {
    $("transcript").textContent = intent.reply;
    return speak(intent.reply);
  }
  openDocument(intent.intent === "EXPLAIN_DOCUMENT" ? "letter" : "bill", intent.reply);
}

function openDocument(mode, reply) {
  ctx.mode = mode;
  $("doc-say").textContent = reply || tr(mode === "letter" ? "show_paper" : "show_bill");
  $("sample-bill").hidden = $("sample-large").hidden = mode !== "bill";
  $("sample-letter").hidden = mode !== "letter";
  show("document");
  speak($("doc-say").textContent);
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = reject;
    r.readAsDataURL(file);
  });
}

// Phone photos are huge; shrink before sending (faster, cheaper, and plenty for reading text)
async function downscale(dataUrl, max = 1600) {
  const img = new Image();
  await new Promise((r, j) => { img.onload = r; img.onerror = j; img.src = dataUrl; });
  const scale = Math.min(1, max / Math.max(img.width, img.height));
  if (scale === 1 && dataUrl.startsWith("data:image/jpeg")) return dataUrl;
  const c = document.createElement("canvas");
  c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale);
  c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
  return c.toDataURL("image/jpeg", 0.88);
}

async function useSample(kind) {
  ctx.sample = kind;
  const url = scenario() === "unreadable" ? "/assets/demo_bill_blurry.png"
    : { bill: "/assets/demo_bill.png", large: "/assets/demo_bill_large.png", letter: "/assets/demo_letter.png" }[kind];
  const blob = await (await fetch(url)).blob();
  readDocument(await fileToDataUrl(blob));
}

async function readDocument(dataUrl) {
  $("preview").src = dataUrl;
  $("eyes-layer").innerHTML = "";
  $("eyes").classList.remove("done");
  show("reading");
  const small = await downscale(dataUrl).catch(() => dataUrl);
  const payload = {
    image_b64: small.split(",")[1], media_type: small.slice(5, small.indexOf(";")), lang: LANG,
    demo_hint: scenario() === "unreadable" ? "unreadable" : ctx.sample === "large" ? "large" : undefined,
  };
  try {
    const [result] = await Promise.all([api(ctx.mode === "letter" ? "/explain" : "/read-bill", payload), sleep(900)]);
    if (!result.readable) return stop({ code: "UNREADABLE", message: result.summary });
    $("eyes").classList.add("done");
    await eyesReveal();
    if (ctx.mode === "letter") return renderExplain(result);
    renderBill(result);
  } catch {
    stop({ code: "UNREADABLE", message: tr("something_wrong") });
  }
}

const SOURCE = { llm: "Read by AI", mock: "Demo mode", fallback: "AI offline — demo data", wallet: "From my documents" };

function renderBill(bill) {
  ctx.bill = bill;
  $("bill-summary").textContent = bill.summary;
  $("bill-amount").textContent = rupees(bill.amount);
  $("bill-due").textContent = fmtDate(bill.due_date);
  $("bill-id").textContent = bill.consumer_id;
  $("bill-provider").textContent = bill.provider || "—";
  $("bill-source").textContent = SOURCE[bill.source] || "";
  renderKnows("bill", bill);
  show("understood");
  const wantsPay = !ctx.intent || ctx.intent.intent === "PAY_BILL";
  speak(bill.summary + (wantsPay ? " " + tr("shall_pay") : ""));
}

function renderExplain(doc) {
  $("ex-title").textContent = doc.title || "";
  $("ex-text").textContent = doc.explanation || "";
  $("ex-source").textContent = SOURCE[doc.source] || "";
  $("ex-actions").innerHTML = (doc.actions || []).map((a) => `<li>${esc(a)}</li>`).join("");
  $("ex-actions-card").hidden = !(doc.actions || []).length && !doc.deadline;
  $("ex-deadline-row").hidden = !doc.deadline;
  $("ex-deadline").textContent = fmtDate(doc.deadline);
  const spoken = [doc.explanation, ...(doc.actions || [])].join(". ");
  $("ex-again").onclick = () => speak(spoken);
  renderKnows("letter", doc);
  show("explain");
  speak(spoken);
}

async function finishExplainOnly() {
  if (ctx.bill) {
    try {
      const task = await api("/tasks", { intent: "READ_BILL", bill: ctx.bill, scenario: scenario(), online: online(), lang: LANG });
      await api(`/tasks/${task.id}/finish`, {});
    } catch { /* not critical */ }
  }
  restart();
  speak(tr("here_whenever"));
}

// ------------------------------------------------------------------ agent runner
// The agent can only send TYPE / CLICK / READ messages to the sandbox. Every step is checked by the
// backend safety engine BEFORE it runs and AFTER we observe the result.
let msgId = 0;
const pending = new Map();
const pageWatchers = new Set();
let readyResolver = null;

window.addEventListener("message", (e) => {
  if (e.origin !== location.origin || !e.data) return;
  const { type, id, observation } = e.data;
  if (type === "saathi-ready" && readyResolver) { readyResolver(e.data); readyResolver = null; }
  if (type === "saathi-observation" && pending.has(id)) { pending.get(id)(e.data); pending.delete(id); }
  if ((type === "saathi-page" || type === "saathi-ready") && observation) pageWatchers.forEach((fn) => fn(observation));
});

function openSandbox(url) {
  return new Promise((resolve, reject) => {
    readyResolver = resolve;
    $("frame-empty").hidden = true;
    $("sandbox").hidden = false;
    $("sandbox").src = url;
    setTimeout(() => { if (readyResolver === resolve) { readyResolver = null; reject(new Error("The service did not open.")); } }, 8000);
  });
}

function sendToSandbox(msg) {
  return new Promise((resolve, reject) => {
    const id = ++msgId;
    pending.set(id, resolve);
    $("sandbox").contentWindow.postMessage({ ...msg, step_id: msg.id, type: "saathi-action", id }, location.origin);
    setTimeout(() => { if (pending.has(id)) { pending.delete(id); reject(new Error("The service stopped responding.")); } }, 10000);
  });
}
const hint = (targets) => $("sandbox").contentWindow?.postMessage({ type: "saathi-hint", targets }, location.origin);

function renderSteps(plan) {
  $("steps").innerHTML = plan.map((s) => `<li id="step-${s.id}"><span class="dot"></span>${esc(s.say)}</li>`).join("");
}
const markStep = (id, cls) => { const li = $("step-" + id); if (li) li.className = cls; };

const LOG_TEXT = {
  OPEN_PAGE: () => "open the payment service", READ: (s) => ({ page: "check which website this is", amount_due: "compare the amount with the paper bill", result: "check the receipt" }[s.target] || "read the page"),
  TYPE: (s) => `type consumer ID ${s.value} (from the bill)`, CLICK: (s) => `click “${({ fetch_bill: "Get bill", pay: "Pay now" })[s.target] || s.target}”`,
  CONFIRM: () => "ask her before paying",
};

async function runAgent() {
  ctx.cancelled = false;
  if (!ctx.stats) ctx.stats = { start: Date.now(), checks: 0 };
  const task = await api("/tasks", { intent: "PAY_BILL", bill: ctx.bill, scenario: scenario(), online: online(), lang: LANG });
  ctx.task = task;
  setState(task.state);
  resetLog();
  log("ALLOW", `plan: ${task.plan.length} fixed steps for ${task.bill.consumer_id}, ${rupees(task.bill.amount)}`);
  renderSteps(task.plan);
  $("work-say").textContent = tr("working");
  show("working");
  speak(tr("taking_care"));

  let lastObs = null;
  for (const step of task.plan) {
    if (ctx.cancelled) return;
    markStep(step.id, "active");
    $("work-say").textContent = step.say;
    await sleep(350);

    // ---- 1. check BEFORE acting
    const pre = await api(`/tasks/${task.id}/check-step`, { step });
    check();
    setState(pre.task_state);
    log(pre.verdict, (pre.verdict === "STOP" ? "refused: " : "") + LOG_TEXT[step.action](step), pre.code);
    if (pre.verdict === "STOP") { markStep(step.id, "failed"); return stop(pre); }
    if (pre.verdict === "CONFIRM") {
      const outcome = await confirmFlow(pre);
      if (outcome.stop) { markStep(step.id, "failed"); return stop(outcome.stop); }
      show("working");
      markStep(step.id, "done");
      continue;
    }

    // ---- 2. act
    let reply;
    try {
      reply = step.action === "OPEN_PAGE" ? { ok: true, ...(await openSandbox(step.target)) } : await sendToSandbox(step);
    } catch (e) {
      markStep(step.id, "failed");
      return stop({ code: "SERVICE_ERROR", message: tr("something_wrong") + " (" + e.message + ")" });
    }
    if (ctx.cancelled) return;
    if (!reply.ok) { markStep(step.id, "failed"); return stop({ code: "SERVICE_ERROR", message: tr("something_wrong") + " (" + reply.error + ")" }); }
    lastObs = reply.observation;

    // ---- 3. check what we now SEE
    let post = await api(`/tasks/${task.id}/observe`, { step, observation: lastObs });
    check();
    setState(post.task_state);
    if (post.verdict === "HANDOFF") {
      log("HANDOFF", `site asks for ${post.field.toUpperCase()}: hand control to her`, "AUTH_HANDOFF");
      markTrick("AUTH_HANDOFF");
      const outcome = await handoffFlow(post);
      if (outcome.stop) { markStep(step.id, "failed"); return stop(outcome.stop); }
      lastObs = outcome.observation;
      post = await api(`/tasks/${task.id}/observe`, { step, observation: lastObs });
      check();
      setState(post.task_state);
      log(post.verdict, "she finished the private step; Saathi resumes");
      show("working");
    } else if (post.verdict === "STOP") {
      const seen = post.code === "UNTRUSTED_SITE" ? `website is ${post.domain}` : post.code === "AMOUNT_MISMATCH"
        ? `site asks ${rupees(post.site_amount)}, bill says ${rupees(post.bill_amount)}` : `saw ${lastObs.page} page`;
      log("STOP", seen, post.code);
    }
    if (post.verdict === "STOP") { markStep(step.id, "failed"); return stop(post); }
    markStep(step.id, "done");
  }

  // ---- success: the backend has already VERIFIED the result against the bill
  log("ALLOW", `receipt ${lastObs.txn_id} = ${rupees(lastObs.amount_paid)} matches the bill`);
  $("ok-amount").textContent = rupees(lastObs.amount_paid);
  $("ok-txn").textContent = lastObs.txn_id;
  renderLearn(task.plan);
  renderProof(lastObs.amount_paid);
  show("success");
  await speak(tr("paid_spoken", { amount: rupees(lastObs.amount_paid) }) + " " + tr("teach_q"));
}

async function cancelTask() {
  ctx.cancelled = true;
  stopListening();
  if (!ctx.task) return restart();
  try {
    const t = await api(`/tasks/${ctx.task.id}/cancel`, {});
    stop(t.stop || { code: "USER_CANCELLED", message: "" });
  } catch {
    restart();
  }
}

// ------------------------------------------------------------------ confirm · family · handoff
function confirmFlow(v) {
  $("confirm-amount").textContent = rupees(v.amount);
  $("confirm-msg").textContent = v.message;
  $("ask-family").hidden = !!v.guardian;           // above the limit, family approval happens anyway
  show("confirm");
  return new Promise((resolve) => {
    let done = false;
    const decide = async (approved, askGuardian = false) => {
      if (done) return;
      done = true;
      stopListening();
      const t = await api(`/tasks/${ctx.task.id}/confirm`, { approved, ask_guardian: askGuardian });
      setState(t.state);
      if (approved) ctx.approvals++;
      log(approved ? "ALLOW" : "STOP", approved ? `she approved ${rupees(v.amount)}` : "she said no", approved ? "PAYMENT_APPROVAL" : "USER_DECLINED");
      if (t.state === "STOPPED") return resolve({ stop: t.stop });
      if (t.state === "WAITING_GUARDIAN") return resolve(await familyFlow(t));
      resolve({ ok: true });
    };
    $("yes").onclick = () => decide(true);
    $("no").onclick = () => decide(false);
    $("ask-family").onclick = () => decide(true, true);
    (async () => {
      await speak(v.message);
      while (!done && SR && !$("mute").checked) {          // voice yes / no — buttons always work too
        try {
          const said = (await listenOnce()).toLowerCase();
          if (done) break;
          if (/\b(yes|yeah|haan|ha|avunu|sare|ok|okay|pay)\b|हाँ|हां|ठीक|అవును|సరే/.test(said)) decide(true);
          else if (/\b(no|nahi|vaddu|stop|cancel)\b|नहीं|रुको|వద్దు|ఆపు/.test(said)) decide(false);
        } catch { break; }
      }
    })();
  });
}

function familyFlow(task) {
  const name = task.guardian?.name || "family";
  $("family-msg").textContent = tr("family_wait", { name });
  $("family-link").textContent = location.origin + "/guardian.html";
  log("CONFIRM", `over ₹5,000: waiting for ${name} to approve`, "PAYMENT_APPROVAL");
  show("family");
  speak(tr("family_wait", { name }));
  return new Promise((resolve) => {
    let finished = false;
    const end = (r) => { if (!finished) { finished = true; clearInterval(timer); resolve(r); } };
    $("family-cancel").onclick = async () => {
      const t = await api(`/tasks/${task.id}/cancel`, {});
      end({ stop: t.stop });
    };
    const timer = setInterval(async () => {
      try {
        const t = await api(`/tasks/${task.id}`);
        if (t.state === "RUNNING") {
          setState("RUNNING");
          ctx.approvals++;
          log("ALLOW", `${name} approved from their phone`);
          await speak(tr("family_approved", { name }));
          end({ ok: true });
        } else if (t.state === "STOPPED") {
          log("STOP", `${name} declined`, "GUARDIAN_DECLINED");
          end({ stop: t.stop });
        }
      } catch { /* keep polling */ }
    }, 1200);
  });
}

function handoffFlow(verdict) {
  $("handoff-msg").textContent = verdict.message;
  show("handoff");
  speak(verdict.message + " " + tr("handoff_wait"));
  hint(["otp", "submit_otp"]);
  return new Promise((resolve) => {
    let finished = false;
    const watcher = (obs) => {
      if (!(obs.fields_requested || []).includes(verdict.field)) end({ observation: obs });
    };
    const end = (r) => { if (!finished) { finished = true; pageWatchers.delete(watcher); hint([]); resolve(r); } };
    pageWatchers.add(watcher);
    $("handoff-cancel").onclick = async () => {
      const t = await api(`/tasks/${ctx.task.id}/cancel`, {});
      end({ stop: t.stop });
    };
  });
}

// ------------------------------------------------------------------ learn mode + guided practice
function renderLearn(plan) {
  ctx.learn = plan.map((s) => s.learn);
  $("learn-steps").innerHTML = ctx.learn.map((l) => `<li>${esc(l)}</li>`).join("");
}

const PRACTICE = {
  home: { now: 2, glow: ["consumer_id", "fetch_bill"] },
  bill: { now: 4, glow: ["pay"] },
  otp: { now: 6, glow: ["otp", "submit_otp"] },
  success: { now: 8, glow: [] },
};

function startPractice() {
  if (!ctx.learn) return;
  $("practise-steps").innerHTML = ctx.learn.map((l, i) => `<li id="pr-${i}">${esc(l)}</li>`).join("");
  show("practise");
  pageWatchers.clear();
  let lastPage = null;
  pageWatchers.add((obs) => {
    const p = PRACTICE[obs.page];
    if (!p || obs.page === lastPage) return;
    lastPage = obs.page;
    ctx.learn.forEach((_, i) => ($("pr-" + i).className = i < p.now ? "did" : i === p.now ? "now" : ""));
    if (obs.page === "bill") $("pr-5").className = "now";
    setTimeout(() => hint(p.glow), 300);
    if (obs.page === "success") speak(tr("practise_done"));
    else speak(ctx.learn[p.now]);
  });
  $("frame-empty").hidden = true;
  $("sandbox").hidden = false;
  $("sandbox").src = "/sandbox/index.html?scenario=" + (scenario() === "otp" ? "otp" : "normal");
  speak(tr("practise_spoken"));
}

// ------------------------------------------------------------------ tasks + wallet
async function openTasks() {
  const tasks = await api("/tasks");
  $("task-list").innerHTML = tasks.length ? tasks.map((t) => `
    <li><span class="t">${tr("bill_word")} · ${rupees(t.bill.amount)}</span>
        <span class="pill ${t.state}">${tr("st_" + t.state)}</span>
        <span class="d">${fmtTime(t.created_at)}${t.result ? " · " + esc(t.result.txn_id) : ""}${t.stop ? " · " + esc(t.stop.message) : ""}</span></li>`).join("")
    : `<li class="empty">${tr("no_tasks")}</li>`;
  show("tasks");
}

async function openWallet() {
  const docs = await api("/documents");
  $("doc-list").innerHTML = docs.length ? docs.map((d, i) => d.kind === "bill" ? `
    <li class="click" data-i="${i}"><span class="t">${tr("bill_word")} · ${rupees(d.amount)}</span>
        <span class="pill">${esc(d.billing_period || "")}</span>
        <span class="d">${esc(d.provider || "")} · ${tr("due")} ${fmtDate(d.due_date)}</span></li>` : `
    <li class="click" data-i="${i}"><span class="t">${esc(d.title)}</span>
        <span class="pill">${tr("letter_word")}</span>
        <span class="d">${d.deadline ? tr("deadline") + " " + fmtDate(d.deadline) : ""}</span></li>`).join("")
    : `<li class="empty">${tr("no_docs")}</li>`;
  $("doc-list").querySelectorAll("li.click").forEach((li) => (li.onclick = () => {
    const d = docs[+li.dataset.i];
    ctx.intent = null;
    ctx.stats = { start: Date.now(), checks: 0 };
    if (d.kind === "bill") {
      renderBill({ ...d, readable: true, source: "wallet",
                   summary: `${tr("bill_word")}: ${rupees(d.amount)} · ${tr("due")} ${fmtDate(d.due_date)}` });
    } else {
      renderExplain({ ...d, source: "wallet" });
    }
  }));
  show("wallet");
}

// ------------------------------------------------------------------ tricks + autopilot
const TRICK_CODE = { mismatch: "AMOUNT_MISMATCH", suspicious: "UNTRUSTED_SITE", otp: "AUTH_HANDOFF", offline: "OFFLINE", unreadable: "UNREADABLE" };
const caught = new Set();
let autopilotRun = 0;

function markTrick(code) {
  if (!ctx.trick || TRICK_CODE[ctx.trick] !== code) return;
  caught.add(ctx.trick);
  document.querySelector(`.trick[data-trick="${ctx.trick}"]`)?.classList.add("caught");
  $("score-n").textContent = caught.size;
  try { sessionStorage.setItem("saathi-caught", JSON.stringify([...caught])); } catch { /* ignore */ }
}

async function typeInto(input, text) {
  input.value = "";
  input.focus();
  for (const ch of text) { input.value += ch; await sleep(28); }
  await sleep(250);
}

// Runs the visible flow up to the point where a human must decide. Autopilot never approves a payment.
async function autopilot({ sample = "bill", request } = {}) {
  const run = ++autopilotRun;
  const alive = () => run === autopilotRun;
  restart();
  await sleep(300);
  await typeInto($("ask"), request || tr("sample_pay"));
  if (!alive()) return;
  handleRequest($("ask").value.trim());
  if ((await waitFor(["document"])) !== "document" || !alive()) return;
  await sleep(900);
  useSample(sample);
  const s = await waitFor(["understood", "stopped"]);
  if (s !== "understood" || !alive()) return;
  await sleep(1800);
  if (alive() && currentScreen() === "understood") $("do-pay").click();
}

function runTrick(kind) {
  $("tricks").hidden = true;
  ctx.trick = kind;
  $("offline").checked = kind === "offline";
  $("scenario").value = kind === "offline" ? "normal" : kind;
  autopilot();
}

// ------------------------------------------------------------------ intro
function hideIntro() {
  const el = $("intro");
  if (el.classList.contains("gone")) return;
  el.classList.add("gone");
  try { sessionStorage.setItem("saathi-intro", "1"); } catch { /* ignore */ }
}
function showIntro() {
  const el = $("intro");
  el.classList.remove("gone");
  el.querySelectorAll(".wordmark span, .intro-story, .intro-line, .intro-go, .intro-hint").forEach((n) => {
    n.style.animation = "none"; void n.offsetWidth; n.style.animation = "";
  });
  $("tricks").hidden = true;
  $("intro-go").focus();
}

// ------------------------------------------------------------------ misc
function restart() {
  stopListening();
  stopMeter();
  window.speechSynthesis?.cancel();
  document.body.classList.remove("speaking");
  pageWatchers.clear();
  ctx.intent = ctx.bill = ctx.task = ctx.sample = ctx.stats = null;
  ctx.cancelled = false;
  ctx.lastState = "CREATED";
  ctx.approvals = 0;
  $("transcript").textContent = "";
  $("ask").value = "";
  $("file").value = "";
  renderStates("CREATED");
  show("welcome");
}

function tickClock() {
  $("clock").textContent = new Date().toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" });
}

// ------------------------------------------------------------------ boot
$("mic").onclick = async () => {
  if (currentRec) return stopListening();
  ctx.trick = null;
  $("mic").classList.add("listening");
  $("orb-label").textContent = tr("listening");
  startMeter();
  try {
    const text = await listenOnce((t) => ($("transcript").textContent = t));
    $("mic").classList.remove("listening");
    stopMeter();
    await handleRequest(text);
  } catch (e) {
    $("transcript").textContent = e.message;
  } finally {
    $("mic").classList.remove("listening");
    $("orb-label").textContent = tr("tap_speak");
    stopMeter();
  }
};
$("ask-go").onclick = () => { ctx.trick = null; handleRequest($("ask").value.trim()); };
$("ask").onkeydown = (e) => { if (e.key === "Enter") { ctx.trick = null; handleRequest($("ask").value.trim()); } };
document.querySelectorAll("[data-sample]").forEach((b) => (b.onclick = () => { ctx.trick = null; handleRequest(tr(b.dataset.sample)); }));
$("sample-bill").onclick = () => useSample("bill");
$("sample-large").onclick = () => useSample("large");
$("sample-letter").onclick = () => useSample("letter");
$("file").onchange = async () => {
  const f = $("file").files[0];
  if (!f) return;
  ctx.sample = null;
  readDocument(await fileToDataUrl(f));
};
$("do-pay").onclick = () => runAgent().catch((e) => stop({ code: "SERVICE_ERROR", message: tr("something_wrong") + " (" + e.message + ")" }));
$("do-done").onclick = finishExplainOnly;
$("work-cancel").onclick = cancelTask;
$("learn-yes").onclick = () => { show("learn"); speak(tr("learn_spoken")); };
$("practise").onclick = startPractice;
$("open-tasks").onclick = () => openTasks().catch(() => {});
$("open-wallet").onclick = () => openWallet().catch(() => {});
document.querySelectorAll(".restart").forEach((b) => (b.onclick = () => { autopilotRun++; restart(); }));
$("lang").onchange = () => setLang($("lang").value);

$("trick-open").onclick = () => { $("tricks").hidden = !$("tricks").hidden; };
$("tricks-close").onclick = () => ($("tricks").hidden = true);
document.querySelectorAll(".trick").forEach((b) => (b.onclick = () => runTrick(b.dataset.trick)));
$("run-demo").onclick = () => { $("tricks").hidden = true; ctx.trick = null; $("offline").checked = false; $("scenario").value = "normal"; autopilot(); };
$("show-intro").onclick = showIntro;
$("intro-go").onclick = hideIntro;
$("intro").onclick = (e) => { if (e.target === $("intro")) hideIntro(); };
document.addEventListener("keydown", (e) => {
  const typing = /INPUT|SELECT|TEXTAREA/.test(document.activeElement?.tagName);
  if (!$("intro").classList.contains("gone") && (e.key === " " || e.key === "Enter")) { e.preventDefault(); hideIntro(); }
  else if (e.key === "Escape") $("tricks").hidden = true;
  else if (!typing && e.key.toLowerCase() === "t") $("tricks").hidden = !$("tricks").hidden;
});

if (window.speechSynthesis) { loadVoices(); speechSynthesis.onvoiceschanged = loadVoices; }
let saved = "en";
try {
  saved = localStorage.getItem("saathi-lang") || "en";
  JSON.parse(sessionStorage.getItem("saathi-caught") || "[]").forEach((k) => {
    caught.add(k); document.querySelector(`.trick[data-trick="${k}"]`)?.classList.add("caught");
  });
  if (sessionStorage.getItem("saathi-intro") || new URLSearchParams(location.search).has("nointro")) {
    $("intro").style.transition = "none";
    $("intro").classList.add("gone");
    requestAnimationFrame(() => requestAnimationFrame(() => ($("intro").style.transition = "")));
  }
} catch { /* storage blocked */ }
$("score-n").textContent = caught.size;
setLang(saved, false);
renderStates("CREATED");
tickClock();
setInterval(tickClock, 15000);

if (location.protocol === "file:") showBanner("file");
else api("/health").then((h) => ($("provider").textContent = `AI provider: ${h.llm_provider}`)).catch(() => {});
