# Saathi — demo script (about 4 minutes) + judge Q&A

## Before you go on stage

- Run `bash run.sh`, open Chrome **full-screen** (`Cmd + Ctrl + F`), and zoom so the whole stage fits (`Cmd + 0`).
- The opening title shows first. Leave it on the projector while you're introduced.
- Open `/guardian.html` on a teammate's phone (the terminal prints the address). Turn the volume up.
- Record a screen capture of the full normal flow beforehand, in case the venue wifi or mic fails.
- Shortcuts: **Space** dismisses the title · **T** opens "Try to trick Saathi" · **Esc** closes it.

---

## 0:00 — The opening title (20 s)

Read the story on screen, then press **Space**.

> "Lakshmi is 68. Her bill is due Friday, her son is 600 km away, and she's afraid of pressing the wrong
> button. Millions of people live like this. This is Saathi."

## 0:20 — "Saathi's eyes" (40 s)

1. Tap the orb and say **"Saathi, please handle my electricity bill."** (Or tap the first suggestion.)
2. Tap **Use the sample bill**. Saathi's eyes lock onto the amount, due date and consumer number, and
   **blur out her name and address**.
   > "Saathi reads only what the task needs. Look at the right-hand panel: her name, address and the
   > photo are never stored."

## 1:00 — The agent at work (60 s)

3. Tap **Pay it for me**. Point at the agent view: Saathi's cursor types the consumer number and clicks
   "Get bill" on its own.
   > "Every step is checked twice, before it runs and after, by plain rules. The AI never decides whether
   > money moves."
4. Saathi stops: **"I am about to pay ₹840… Do you approve?"** Say **"Yes."**
5. Success. Point at the proof card: seconds taken, safety checks passed, **0 passwords typed by Saathi**,
   one human approval.

## 2:00 — Try to trick Saathi (60 s): the moment judges remember

6. Press **T**. Hand the laptop to a judge if you can.
   > "Don't trust us. Try to trick it."
7. **Inflate the amount**: the website asks ₹8,400. Saathi stops and shows **₹840 vs ₹8,400** side by side.
8. **Swap in a fake website**: Saathi refuses `electricity-pay-demo.xyz` before typing anything.
9. Show the score: "2 of 5 tricks caught". Mention the others: OTP, no internet, blurry photo.

## 3:00 — Learn Mode + family (40 s)

10. Run the normal flow again (Presenter settings → "Run the main demo automatically"), approve, and tap
    **Yes, teach me** → **Practise it now**. The glowing box guides her through it herself.
    > "Saathi doesn't make her dependent. Next time, she does it herself."
11. Optional: **Use the large sample bill (₹6,500)**. The teammate's phone gets the request and taps Approve.

## 3:40 — Telugu (10 s) and close (10 s)

12. Switch to **తెలుగు** and tap the letter suggestion: a pension notice explained in Telugu.

> "One agent, one task, done safely from start to finish, in her language. The same engine extends to
> water, gas, pensions and government services."

---

## Judge Q&A

**Where did you get access to the electricity board or a bank?**
We didn't, by design. The Saathi Service Sandbox stands in for an external service, so we can show the
agent, safety and verification architecture without touching real money or government systems.
A real deployment would use official APIs or authorised interfaces.

**What if the AI hallucinates an amount?**
The AI only reads and explains. The plan is fixed code, and the safety engine is plain rules: the
website's amount must match the paper bill, anything the agent types must come from the bill, and the
receipt must match too. The AI never decides whether money moves.

**What about OTP, PIN and CAPTCHA?**
The agent is not allowed to type them, and that is enforced in code. Saathi hands control to the person,
waits, then verifies the result.

**Isn't the autopilot cheating?**
Autopilot only types the request and picks the sample bill. It cannot approve a payment: that always
needs a human tap or "yes".

**Privacy?**
Synthetic data only. Saathi keeps the fields a task needs (amount, due date, consumer number), never the
photo, name or address, and you can see that live on screen. Production would add encryption, consent
and retention limits.

**No internet?**
Reading and explaining work in demo mode. Payments need a connection, and Saathi says so.

**Why AI at all?**
Understanding a vague spoken request in three languages, and reading messy photos of real bills and
letters. Everything that can be rules (safety, planning) is rules.

**What did you not build?**
Real bank or UPI payments, real government portals, Aadhaar, OTP automation (deliberately), and control
of arbitrary Android apps. We chose one complete, safe workflow over six half-built modules.
