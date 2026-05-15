# AI System — FinTrust AI

How the Groq + Llama 3.3 70B integration works, including prompts, response parsing, and fallback logic.

---

## Overview

FinTrust AI uses the **Groq API** with the `llama-3.3-70b-versatile` model for three distinct AI tasks:

| Task | Endpoint | System Prompt |
|------|----------|---------------|
| Credit Scoring | `POST /credit-score/analyze/` | `CREDIT_SYSTEM_PROMPT` |
| Fraud Detection | `POST /fraud/analyze/` | `FRAUD_SYSTEM_PROMPT` |
| Portfolio Insights | `POST /ai/insights/` | `INSIGHTS_SYSTEM_PROMPT` |

All AI calls are made in `apps/ai_insights/services/groq_service.py`.

---

## Model Configuration

```python
MODEL = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')

client.chat.completions.create(
    model=MODEL,
    messages=[...],
    temperature=0.2,   # Low temperature = consistent, deterministic outputs
    max_tokens=400,    # Short JSON responses
)
```

`temperature=0.2` ensures the model returns stable, consistent JSON rather than creative text. This is critical for parsing.

---

## System Prompts

### Credit Scoring Prompt

```
You are an African fintech credit analyst specialized in mobile money behavior analysis.
Analyze the customer financial behavior data and return ONLY a valid JSON object with no other text:
{
  "risk_score": <integer 0-100>,
  "repayment_probability": <float 0.0-1.0>,
  "explanation": "<2 sentences max, professional tone>",
  "recommended_loan": <integer XAF amount>
}
Risk score: 0=very high risk, 100=very safe. Be concise and professional.
```

**User message format:**
```
Monthly income: {monthly_income} XAF
Mobile money frequency: {mobile_money_frequency} transactions/month
Late payments: {late_payments}
Account age: {account_age_months} months
```

---

### Fraud Detection Prompt

```
You are a banking fraud detection AI specialized in African mobile money transactions.
Analyze the transaction and return ONLY a valid JSON object with no other text:
{
  "fraud_probability": <integer 0-100>,
  "urgency": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "indicators": ["<indicator1>", "<indicator2>"],
  "explanation": "<2 sentences max>",
  "action": "<ALLOW|FLAG|BLOCK>"
}
```

**User message format:**
```
Amount: {amount} XAF
Location: {location}
Device change: {device_change}
Time: {timestamp}
User avg transaction: {avg_amount} XAF
```

---

### Portfolio Insights Prompt

```
You are an AI financial advisor for African banking ecosystems.
Return ONLY a valid JSON object with no other text:
{
  "summary": "<3 sentences executive overview>",
  "recommendations": ["<rec1>", "<rec2>", "<rec3>"],
  "risk_level": "<LOW|MEDIUM|HIGH>",
  "opportunities": ["<opp1>", "<opp2>"]
}
```

**User message format:**
```
Total transactions: {total_transactions}
Average risk score: {avg_risk_score}
Active fraud alerts: {active_alerts}
Total loan volume: {total_loans} XAF
High risk customers: {high_risk_count}
```

---

## Response Parsing

The `_call_groq()` function handles both clean JSON and markdown-fenced JSON:

```python
def _call_groq(system_prompt: str, user_message: str) -> dict:
    resp = client.chat.completions.create(...)
    text = resp.choices[0].message.content.strip()

    # Strip markdown code fences if present (```json ... ```)
    if text.startswith('```'):
        text = text.split('```')[1]
        if text.startswith('json'):
            text = text[4:]

    return json.loads(text)
```

This handles responses like:
```
```json
{"risk_score": 81, ...}
```
```
as well as bare JSON.

---

## Fallback Logic

Every AI call is wrapped in a `safe_*` function. If Groq fails (network error, API rate limit, JSON parse error, timeout), a deterministic fallback activates:

### Credit Score Fallback

```python
def safe_analyze_credit(data: dict) -> dict:
    try:
        return analyze_credit(data)
    except Exception as e:
        income = data.get('monthly_income', 100000)
        late = data.get('late_payments', 0)
        score = min(95, max(15, 70 + (income // 10000) - (late * 8)))
        return {
            'risk_score': score,
            'repayment_probability': round(score / 100 * 0.95, 2),
            'explanation': 'Stable mobile money transaction history with consistent activity patterns detected.',
            'recommended_loan': int(income * 1.5),
        }
```

**Formula:** `score = clamp(70 + income/10000 - late_payments×8, 15, 95)`

### Fraud Detection Fallback

```python
prob = 15 (base)
prob += 40  # if device_change == True
prob += 25  # if amount > 500,000 XAF

urgency = LOW|MEDIUM|HIGH|CRITICAL based on prob thresholds
action  = ALLOW|FLAG|BLOCK based on prob thresholds
```

### Insights Fallback

Returns a hardcoded but realistic-sounding portfolio summary with African market context.

---

## Groq API Setup

1. Get a free API key at [console.groq.com](https://console.groq.com)
2. Set `GROQ_API_KEY=gsk_xxxxx` in your `.env`
3. The model `llama-3.3-70b-versatile` is available on the free tier

**Rate limits (free tier):** ~30 requests/minute, 14,400 requests/day. For a hackathon demo, this is more than sufficient.

**Latency:** Groq is exceptionally fast — typical response time is **200–800ms** even for a 70B parameter model.

---

## Adding New AI Features

To add a new AI capability:

1. Add a system prompt constant in `groq_service.py`
2. Add an `analyze_*` function that builds the user message and calls `_call_groq()`
3. Add a `safe_analyze_*` wrapper with deterministic fallback
4. Create a new view in the appropriate app
5. Register the URL in `config/api_urls.py`

Example skeleton:

```python
MY_SYSTEM_PROMPT = """You are a... Return ONLY JSON: {"field": value}"""

def analyze_something(data: dict) -> dict:
    prompt = f"Input: {data.get('key', 'default')}"
    return _call_groq(MY_SYSTEM_PROMPT, prompt)

def safe_analyze_something(data: dict) -> dict:
    try:
        return analyze_something(data)
    except Exception:
        return {"field": "fallback_value"}
```

---

## Extending the Dataset System

`apps/ai_insights/datasets.py` provides `load_dataset_entries(request)` — it reads from:
1. JSON body (list of objects)
2. `multipart/form-data` with a `file` field (`.csv` or `.xlsx`)

The templates endpoint (`/datasets/templates/{type}/{format}/`) returns downloadable sample files so users can see exactly what column headers and data formats are expected.
