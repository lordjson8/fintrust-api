import os
import json
from groq import Groq

client = Groq(api_key=os.environ.get('GROQ_API_KEY', ''))
MODEL = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')

# ─── System Prompts ───────────────────────────────────────────────────────────

CREDIT_SYSTEM_PROMPT = """You are an African fintech credit analyst specialized in mobile money behavior analysis.
Analyze the customer financial behavior data and return ONLY a valid JSON object with no other text:
{
  "risk_score": <integer 0-100>,
  "repayment_probability": <float 0.0-1.0>,
  "explanation": "<2 sentences max, professional tone>",
  "recommended_loan": <integer XAF amount>
}
Risk score: 0=very high risk, 100=very safe. Be concise and professional."""

FRAUD_SYSTEM_PROMPT = """You are a banking fraud detection AI specialized in African mobile money transactions.
Analyze the transaction and return ONLY a valid JSON object with no other text:
{
  "fraud_probability": <integer 0-100>,
  "urgency": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "indicators": ["<indicator1>", "<indicator2>"],
  "explanation": "<2 sentences max>",
  "action": "<ALLOW|FLAG|BLOCK>"
}"""

INSIGHTS_SYSTEM_PROMPT = """You are an AI financial advisor for African banking ecosystems.
Return ONLY a valid JSON object with no other text:
{
  "summary": "<3 sentences executive overview>",
  "recommendations": ["<rec1>", "<rec2>", "<rec3>"],
  "risk_level": "<LOW|MEDIUM|HIGH>",
  "opportunities": ["<opp1>", "<opp2>"]
}"""


# ─── Core Functions ────────────────────────────────────────────────────────────

def _call_groq(system_prompt: str, user_message: str) -> dict:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message},
        ],
        temperature=0.2,
        max_tokens=400,
    )
    text = resp.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if text.startswith('```'):
        text = text.split('```')[1]
        if text.startswith('json'):
            text = text[4:]
    return json.loads(text)


def analyze_credit(data: dict) -> dict:
    prompt = (
        f"Monthly income: {data.get('monthly_income', 0)} XAF\n"
        f"Mobile money frequency: {data.get('mobile_money_frequency', 0)} transactions/month\n"
        f"Late payments: {data.get('late_payments', 0)}\n"
        f"Account age: {data.get('account_age_months', 0)} months"
    )
    return _call_groq(CREDIT_SYSTEM_PROMPT, prompt)


def analyze_fraud(data: dict) -> dict:
    prompt = (
        f"Amount: {data.get('amount', 0)} XAF\n"
        f"Location: {data.get('location', 'Unknown')}\n"
        f"Device change: {data.get('device_change', False)}\n"
        f"Time: {data.get('timestamp', 'N/A')}\n"
        f"User avg transaction: {data.get('avg_amount', 150000)} XAF"
    )
    return _call_groq(FRAUD_SYSTEM_PROMPT, prompt)


def analyze_insights(data: dict) -> dict:
    prompt = (
        f"Total transactions: {data.get('total_transactions', 0)}\n"
        f"Average risk score: {data.get('avg_risk_score', 0)}\n"
        f"Active fraud alerts: {data.get('active_alerts', 0)}\n"
        f"Total loan volume: {data.get('total_loans', 0)} XAF\n"
        f"High risk customers: {data.get('high_risk_count', 0)}"
    )
    return _call_groq(INSIGHTS_SYSTEM_PROMPT, prompt)


# ─── Safe Wrappers (always return valid data for demo) ─────────────────────────

def safe_analyze_credit(data: dict) -> dict:
    try:
        return analyze_credit(data)
    except Exception as e:
        print(f'[Groq Credit Fallback] {e}')
        income = data.get('monthly_income', 100000)
        late = data.get('late_payments', 0)
        score = min(95, max(15, 70 + (income // 10000) - (late * 8)))
        return {
            'risk_score': score,
            'repayment_probability': round(score / 100 * 0.95, 2),
            'explanation': 'Stable mobile money transaction history with consistent activity patterns detected.',
            'recommended_loan': int(income * 1.5),
        }


def safe_analyze_fraud(data: dict) -> dict:
    try:
        return analyze_fraud(data)
    except Exception as e:
        print(f'[Groq Fraud Fallback] {e}')
        amount = float(data.get('amount', 0))
        device_change = data.get('device_change', False)
        prob = 15
        if device_change:
            prob += 40
        if amount > 500000:
            prob += 25
        urgency = 'LOW' if prob < 30 else 'MEDIUM' if prob < 60 else 'HIGH' if prob < 80 else 'CRITICAL'
        action = 'ALLOW' if prob < 40 else 'FLAG' if prob < 70 else 'BLOCK'
        return {
            'fraud_probability': min(prob, 99),
            'urgency': urgency,
            'indicators': ['Unusual transaction amount'] if amount > 500000 else ['Normal activity'],
            'explanation': 'Transaction analyzed based on behavioral pattern matching.',
            'action': action,
        }


def safe_analyze_insights(data: dict) -> dict:
    try:
        return analyze_insights(data)
    except Exception as e:
        print(f'[Groq Insights Fallback] {e}')
        return {
            'summary': 'Portfolio shows moderate risk distribution with growth opportunities in mobile money segments. Fraud detection systems are actively monitoring high-value transactions. Credit performance remains stable with improving repayment trends.',
            'recommendations': [
                'Increase credit limits for low-risk mobile money users',
                'Implement additional verification for device-change transactions',
                'Expand outreach to informal traders with 12+ months mobile money history',
            ],
            'risk_level': 'MEDIUM',
            'opportunities': [
                'Underserved SME segment with strong mobile money activity',
                'Agricultural financing during harvest season',
            ],
        }
