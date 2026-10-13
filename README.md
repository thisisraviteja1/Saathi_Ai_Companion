<div align="center">

# 🧡 Saathi · साथी · సాథీ

### An AI companion for everything digital

**You don't need to learn the app. Just tell Saathi what you need.**

Voice-first in English, Hindi and Telugu · Reads bills and letters from a photo · Pays safely with family approval · Finds government schemes · Teaches you to do it yourself

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Starlette](https://img.shields.io/badge/Backend-Starlette-2E8B57)
![JavaScript](https://img.shields.io/badge/Frontend-Vanilla%20JS-F7DF1E?logo=javascript&logoColor=black)
![Gemini](https://img.shields.io/badge/AI-Gemini%20%7C%20Claude%20%7C%20OpenAI-F4A71D)
![Tests](https://img.shields.io/badge/tests-24%20passing-2E8B57)
![HACKVIBE 2.0](https://img.shields.io/badge/HACKVIBE-2.0-D2353A)

</div>

---

## 📖 The story

Lakshmi is 68. Her electricity bill has just arrived. She has a smartphone, but she doesn't know which app to open, which button to press, or whether it's safe. So she calls her son and waits.

Tomorrow it's a train ticket. Then a government scheme. Then checking an application. **Every time, she depends on someone else.**

Millions of people own smartphones but can't use them for the things that matter. **Having a smartphone doesn't mean having digital access.**

## 💡 What Saathi does

Instead of asking people to learn technology, **Saathi brings technology to the person.** She simply says:

> *"Saathi, my electricity bill has come. Can you help me?"*

Saathi reads the bill from a photo, explains it in her language, asks before paying, gets a family member's approval for large amounts, pays step by step on screen, checks the receipt matches the bill, tells her aloud that it's done, and then offers to **teach her to do it herself next time**.

## ✨ Features

| | Feature | What the person experiences |
|---|---|---|
| 🎤 | **Voice in 3 languages** | Speak or type in English, हिन्दी or తెలుగు; Saathi answers aloud in the same language |
| 📷 | **Reads anything** | Photo of a bill, letter or notice → what it says, what to do, and the deadline |
| 🤖 | **Does it with you** | Pays a bill step by step with a visible cursor, so nothing happens behind her back |
| 🛡️ | **Safety engine** | Checks every step before *and* after; stops on a wrong amount, a fake website or no internet |
| 🔐 | **Private-step handoff** | For an OTP, PIN or password, Saathi stops and lets the person type it |
| 👨‍👩‍👦 | **Family approval** | Bills over ₹5,000 need a tap from a family member on their own phone |
| ✅ | **Verification** | Reports success only when the receipt matches the paper bill |
| 🎓 | **Learn mode** | Explains the steps in plain words, then guides practice with glowing hints |
| 🏛️ | **Benefits finder** | Show a ration card or answer 8 questions → eligible schemes, why, and how to apply (7 central schemes) |
| 🔒 | **Private by design** | Photos are never stored; personal details are blurred, dropped, or encrypted in the browser |

## 🧠 Key design principle

> **AI understands. Rules decide.**

The AI model only *understands* the request and *reads* documents. It never decides whether money moves or who is eligible:

- **Plans** are fixed code (`backend/planner.py`)
- **Safety** is a deterministic rules engine (`backend/safety.py`) that returns `ALLOW` / `CONFIRM` / `HANDOFF` / `STOP`
- **Eligibility** comes from a reviewable rules file (`frontend/benefits/schemes.json`) evaluated in the browser

If the AI call fails, Saathi falls back to demo data **and says so on screen**.

## 🏗️ How it works

```
🎤 voice / photo
      │
      ▼
  AI understands ──► 📄 letter  ──► plain-language explanation + deadline
      │
      ├──► 🧾 bill ──► fixed 8-step plan
      │                  for every step:  safety check (before) → act → observe (after)
      │                  CONFIRM  → she says yes → family approves (if large)
      │                  HANDOFF  → she types the OTP herself
      │                  receipt == bill → ✅ VERIFIED → 🔊 tells her → 🎓 Learn mode
      │
      └──► 🏛️ benefits ──► card photo (nothing stored) → answers encrypted in browser
                            → rules matched in browser → schemes + how to apply
```

## 🚀 Run it locally

**Requirements:** Python 3.10+ and Google Chrome (Chrome is needed for voice input).

```bash
git clone https://github.com/<your-username>/saathi.git
cd saathi
bash run.sh          # Mac / Linux
```

On **Windows**, double-click `run.bat`.

The first run sets everything up in about 30 seconds and opens **http://localhost:8000**. Keep the terminal open; stop with `Ctrl + C`.

### 🔑 Connect an AI model (optional)

Saathi runs **without any API key** in demo mode, using the sample documents. To read **your own photos**, connect a model:

```bash
bash setup_ai.sh     # choose Gemini / Claude / OpenAI, paste your key, and it tests it on the sample bill
```

Or copy `.env.example` to `.env` and fill it in:

```env
LLM_PROVIDER=gemini          # gemini | anthropic | openai | mock
GEMINI_API_KEY=your-key-here
LLM_TIMEOUT=30
```

> ⚠️ Never commit your `.env` file. It is listed in `.gitignore`.

### 🧪 Tests

```bash
python3 tests/test_safety.py      # 17 safety tests: attack scenarios, translations, data minimisation
python3 tests/test_benefits.py    # 7 eligibility-rule tests
```

## 🎬 Demo scenarios

Press **T** in the app to open the "Try to trick Saathi" judge panel.

| Scenario | What happens | Safety rule |
|---|---|---|
| Normal ₹840 bill | Asks → pays → verifies → offers Learn mode | — |
| Large ₹6,500 bill | Waits for family approval on `/guardian.html` | Family approval |
| Inflated amount | Site asks ₹8,400 → Saathi stops and shows ₹840 vs ₹8,400 | `AMOUNT_MISMATCH` |
| Site asks for OTP | Hands over; she types it; Saathi verifies | `AUTH_HANDOFF` |
| Fake website | Refuses an untrusted domain | `UNTRUSTED_SITE` |
| Blurry photo | Asks for a clearer photo | `UNREADABLE` |
| Internet cut | Explains the bill but won't pay | `OFFLINE` |
| "What government help can I get?" | Reads a household card → PM-JAY, old-age pension | Rules in the browser |

**Family approval on a real phone:** the terminal prints an address like `http://192.168.1.5:8000/guardian.html`. Open it on a phone on the same Wi-Fi.

## 📁 Project structure

```
saathi/
├── backend/
│   ├── main.py          # API server (Starlette + uvicorn)
│   ├── llm.py           # Gemini / Claude / OpenAI-compatible / mock (stdlib only)
│   ├── prompts.py       # prompts + JSON contracts
│   ├── safety.py        # deterministic safety engine
│   ├── planner.py       # fixed 8-step plan + task state machine
│   ├── store.py         # tasks, document wallet, family requests
│   ├── i18n.py          # everything Saathi says, in en / hi / te
│   └── check_ai.py      # tests your AI key on the sample bill
├── frontend/
│   ├── index.html       # the companion (phone) + judge view
│   ├── app.js           # voice, Saathi's eyes, agent runner, handoff, Learn mode
│   ├── benefits.js      # benefits finder + rules engine
│   ├── vault.js         # Web Crypto (AES-GCM) vault in IndexedDB
│   ├── guardian.html    # family member's approval page
│   ├── sandbox/         # demo bill-payment service
│   └── benefits/schemes.json   # eligibility rules for 7 central schemes
├── assets/              # synthetic sample bills, letter and ration card
├── tests/               # 24 automated tests
├── docs/                # implementation plan (PDF) + demo script
├── run.sh / run.bat     # one-command launchers
└── setup_ai.sh          # connect an AI model
```

## 🛠️ Tech stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, vanilla JavaScript, Web Speech API, Web Crypto API, IndexedDB |
| Backend | Python, Starlette, uvicorn |
| AI | Vision-language models: Google Gemini (default), Anthropic Claude, or any OpenAI-compatible API |
| Safety | Deterministic rules engine (no AI in the decision path) |

## 🗺️ Roadmap

- [x] Voice companion in English, Hindi and Telugu
- [x] Photo reading for bills, letters and ID cards
- [x] Safe bill payment on a demo service with family approval
- [x] Benefits finder for 7 central schemes
- [x] Learn mode
- [ ] Real bill payments through BBPS + UPI
- [ ] Document wallet
- [ ] Guided ticket booking
- [ ] Supervised pilot in one state

## ⚠️ Disclaimer

This is a hackathon prototype. Payments run on a **demo service**, so no real money moves. All sample documents are synthetic. Scheme eligibility rules are for demonstration only and must be reviewed by a person before real use.

## 👥 Team

Built at **HACKVIBE 2.0** by:

- Bharath Pole · [GitHub](https://github.com/Bharath0408) · [LinkedIn](https://linkedin.com/in/bharath-pole)
- *Teammate 2*
- *Teammate 3*

---

<div align="center">

**Technology shouldn't leave people behind. It should adapt to them.**

</div>
