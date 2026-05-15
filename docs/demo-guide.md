# Demo Guide — FinTrust AI Hackathon

A step-by-step script for delivering a compelling 5–10 minute demo. Follow this order for maximum impact.

---

## Demo Setup Checklist

Before presenting:

- [ ] Backend running (local or Railway)
- [ ] Frontend running at `localhost:3000` or Vercel URL
- [ ] `python manage.py seed_demo` has been run
- [ ] Browser window is ready at `/login`
- [ ] Postman collection is loaded with `base_url` set (for technical Q&A)
- [ ] Screen is at 1280px+ width — sidebar is visible

---

## The Story

> *"Africa has 700 million mobile money users. Yet 80% are denied loans because they lack a credit history. FinTrust AI changes that — using the financial behavior that already exists."*

---

## Act 1 — Login (30 seconds)

**Navigate to:** `/login`

Log in as the admin:
- Email: `admin@fintrust.ai`
- Password: `admin1234`

**What to say:**
> "An analyst or bank officer logs in. They immediately see the platform is designed for professionals — not a generic dashboard."

---

## Act 2 — Dashboard Overview (60 seconds)

**Navigate to:** `/dashboard` (auto-redirect after login)

**Point out:**
- **4 KPI cards** — Total Transactions, Average Risk Score, Active Fraud Alerts, High Risk Customers
- **Risk Distribution donut chart** — shows the portfolio split (green/yellow/red)
- **Transaction Volume bar chart**
- **Recent Fraud Alerts** — red CRITICAL/HIGH badges visible immediately

**What to say:**
> "In one screen, a risk manager sees the health of their entire loan portfolio. Risk scores color-coded in real time. Fraud alerts surfaced immediately — no digging required."

**Key talking point:** The platform auto-refreshes every 30 seconds. This is live data.

---

## Act 3 — AI Credit Scoring (2 minutes)

**Navigate to:** `/risk-analysis`

Fill in a customer profile:

| Field | Value |
|-------|-------|
| Monthly Income | `180,000` |
| Mobile Money Frequency | `52` |
| Late Payments | `1` |
| Account Age | `18` months |

Click **Analyze Risk**.

**Wait for AI response (~1 second on Groq).**

**Point out the result:**
- Risk Score: **81/100** (green — Low Risk)
- Repayment Probability: **87%**
- Recommended Loan: **270,000 XAF**
- AI Explanation: the two-sentence reasoning from Llama 3.3

**What to say:**
> "In under 2 seconds, the AI has assessed this customer using their mobile money behavior. No salary slip. No collateral. Just their actual financial behavior — and a clear, explainable recommendation."

**Then show a high-risk profile:**

| Field | Value |
|-------|-------|
| Monthly Income | `60,000` |
| Mobile Money Frequency | `12` |
| Late Payments | `8` |
| Account Age | `3` months |

**Result:** Score ~25, red badge, low loan recommendation.

> "The same system flags this profile as high risk — protecting the institution from bad loans."

---

## Act 4 — Fraud Detection (90 seconds)

**Navigate to:** `/alerts`

Show the existing fraud alert list — point out the CRITICAL/HIGH urgency badges.

**Navigate to:** `/risk-analysis` (Fraud tab) or wherever fraud form is

Submit a suspicious transaction:

| Field | Value |
|-------|-------|
| Amount | `750,000 XAF` |
| Location | `Yaoundé` |
| Device Change | ✅ Yes |
| Average Amount | `90,000 XAF` |

**What to say:**
> "A 750,000 XAF transfer — 8x this customer's average — with a simultaneous device change. Classic fraud pattern."

**AI response:**
- Fraud Probability: **82%**
- Urgency: **HIGH**
- Action: **BLOCK**
- Indicators: "Amount 8x above average", "Device change detected"

> "The system instantly recommends blocking this transaction. The analyst can act in seconds, not days."

**Then show a clean transaction:**

| Field | Value |
|-------|-------|
| Amount | `45,000 XAF` |
| Device Change | ❌ No |
| Average Amount | `50,000 XAF` |

**Result:** 12% fraud probability, ALLOW. 

> "Normal transaction — ALLOW. The system doesn't flag everything. It's precise."

---

## Act 5 — AI Portfolio Insights (45 seconds)

**Navigate to:** `/ai-insights`

Click **Generate Insights**.

**Point out:**
- Executive summary (3 sentences)
- Risk level classification
- 3 concrete recommendations
- 2 identified opportunities

**What to say:**
> "Finally, the AI synthesizes everything — all customers, all transactions, all fraud signals — into an executive briefing. A CEO or risk committee can read this in 30 seconds and know exactly where their portfolio stands."

---

## Act 6 — Analytics (30 seconds)

**Navigate to:** `/analytics`

Point to charts:
- Transaction volume by type
- Risk score distribution
- Payment method breakdown

> "The analytics page gives the data team the charts they need for reporting — all generated from real transaction behavior, not survey data."

---

## Closing Statement

> "FinTrust AI turns mobile money data into credit intelligence. We're giving African financial institutions the tools to say YES to customers they've been forced to reject — safely, quickly, and with AI they can trust and explain."

---

## Technical Q&A Cheat Sheet

**"What AI model does this use?"**
> Groq's Llama 3.3 70B — the same open model architecture used by Meta, running on Groq's ultra-fast inference hardware. Response time under 1 second.

**"What if Groq is down?"**
> We built deterministic fallback logic — the system always returns a result, even without AI. Analysts never see a blank screen.

**"How does authentication work?"**
> JWT tokens via Django REST Framework + SimpleJWT. 8-hour access tokens, 7-day refresh. Role-based: admin sees everything, analyst sees only their data.

**"How does the fraud detection handle new patterns it hasn't seen?"**
> It uses a large language model, so it reasons about the signals rather than matching against fixed rules. Device change + unusual amount + new location are all contextually understood.

**"Can this work with CSV/XLSX bulk uploads?"**
> Yes. The batch endpoints accept JSON arrays, CSV, or XLSX. Perfect for institutions importing historical customer data.

**"What database?"**
> PostgreSQL on Railway. Production-grade, managed, auto-scaled.

**"Is the API documented?"**
> Full OpenAPI 3.0 spec via drf-spectacular. Available at `/` in dev mode (Swagger UI) or `/api/schema/redoc/` (ReDoc).

---

## Postman Full Demo Flow

For a technical audience, run the **🔁 Full Demo Flow** folder in Postman:

1. Step 1 — Login as Analyst
2. Step 2 — Create Transaction
3. Step 3 — AI Credit Score
4. Step 4 — Fraud Detection
5. Step 5 — Dashboard (shows updated KPIs)

This shows the complete end-to-end flow in the console with logged scores, amounts, and probabilities.
