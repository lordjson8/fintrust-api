# API Reference — FinTrust AI

**Base URL:** `http://localhost:8000/api/v1/`  
**Production:** `https://your-app.railway.app/api/v1/`  
**OpenAPI Schema:** `GET /api/schema/` (DEBUG only)  
**Swagger UI:** `GET /` (DEBUG only)  
**ReDoc:** `GET /api/schema/redoc/` (DEBUG only)

---

## Authentication

All endpoints except `/auth/login/`, `/auth/register/`, and `/auth/refresh/` require a Bearer token.

```
Authorization: Bearer <access_token>
```

Tokens are JWT. Access tokens expire after **8 hours**; refresh tokens after **7 days**. On refresh, a new refresh token is also issued (`ROTATE_REFRESH_TOKENS = True`).

---

## Endpoints

---

### 🔐 Authentication

#### POST `/auth/login/`

Authenticate and receive JWT tokens.

**Permissions:** Public

**Request body:**

```json
{
  "email": "admin@fintrust.ai",
  "password": "admin1234"
}
```

**Response `200 OK`:**

```json
{
  "access": "eyJhbGci...",
  "refresh": "eyJhbGci...",
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "admin@fintrust.ai",
    "full_name": "Admin User",
    "role": "admin"
  }
}
```

**Error responses:**

| Status | Condition | Body |
|--------|-----------|------|
| `400` | Missing email or password | `{"error": "Email and password are required"}` |
| `401` | Wrong credentials | `{"error": "Invalid credentials"}` |

---

#### POST `/auth/register/`

Register a new analyst account.

**Permissions:** Public  
**Note:** All registered users get `role: "analyst"` regardless of input.

**Request body:**

```json
{
  "email": "new.analyst@demo.com",
  "password": "demo1234",
  "full_name": "Test Analyst"
}
```

**Response `201 Created`:**

```json
{
  "access": "eyJhbGci...",
  "refresh": "eyJhbGci...",
  "user": {
    "id": "...",
    "email": "new.analyst@demo.com",
    "full_name": "Test Analyst",
    "role": "analyst"
  }
}
```

**Error responses:**

| Status | Condition | Body |
|--------|-----------|------|
| `400` | Missing fields | `{"error": "email, password, and full_name are required"}` |
| `400` | Duplicate email | `{"error": "Email already registered"}` |

---

#### POST `/auth/refresh/`

Get a new access token using a refresh token.

**Permissions:** Public

**Request body:**

```json
{
  "refresh": "eyJhbGci..."
}
```

**Response `200 OK`:**

```json
{
  "access": "eyJhbGci..."
}
```

---

### 💳 Transactions

#### GET `/transactions/`

List transactions. Admins see all; analysts see only their own. Limited to the 50 most recent.

**Permissions:** Authenticated  

**Response `200 OK`:**

```json
[
  {
    "id": "3fa85f64-...",
    "user": "uuid",
    "user_name": "Jean Pierre Mvondo",
    "amount": "125000.00",
    "type": "credit",
    "payment_method": "mobile_money",
    "location": "Yaoundé",
    "timestamp": "2026-05-15T10:30:00Z",
    "device_change": false,
    "fraud_alert": {
      "fraud_probability": 12,
      "urgency": "LOW",
      "action": "ALLOW"
    }
  }
]
```

`fraud_alert` is `null` if no fraud analysis has been run on that transaction.

**Transaction type values:** `credit` | `debit` | `transfer`  
**Payment method values:** `mobile_money` | `bank` | `cash`

---

#### POST `/transactions/`

Create a single transaction.

**Permissions:** Authenticated  
**Note:** Analysts can only create transactions for themselves (the `user` field is overridden). Admins can specify any `user` UUID.

**Request body:**

```json
{
  "user": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "amount": 125000,
  "type": "credit",
  "payment_method": "mobile_money",
  "location": "Yaoundé",
  "device_change": false
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `user` | UUID | Yes (admin) | Overridden to current user for analysts |
| `amount` | decimal | Yes | In XAF |
| `type` | string | Yes | `credit` / `debit` / `transfer` |
| `payment_method` | string | No | Default: `mobile_money` |
| `location` | string | No | Default: `Yaoundé` |
| `device_change` | boolean | No | Default: `false` |

**Response `201 Created`:** Transaction object (same shape as GET list item)

**Error `400`:** `{"type": ["Value 'invalid_type' is not a valid choice."]}` 

---

#### POST `/transactions/batch/`

Bulk-import transactions from a JSON array, CSV, or XLSX file.

**Permissions:** Authenticated

**Option A — JSON body:**
```json
[
  {"amount": 50000, "type": "credit", "payment_method": "mobile_money", "location": "Douala"},
  {"amount": 80000, "type": "debit", "payment_method": "bank", "location": "Yaoundé"}
]
```

**Option B — File upload:**  
Send `multipart/form-data` with a `file` field containing a `.csv` or `.xlsx`. The file must have column headers matching the field names above.

**Response `200 OK`:**

```json
{
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "results": [
    {"row": 1, "status": "success", "result": { ...transaction... }},
    {"row": 2, "status": "success", "result": { ...transaction... }}
  ]
}
```

---

### 🧠 Credit Scoring

#### POST `/credit-score/analyze/`

Run AI credit risk analysis on a customer's financial profile.

**Permissions:** Authenticated  
**AI Model:** Groq `llama-3.3-70b-versatile`  
**Fallback:** Deterministic formula if Groq is unavailable.

**Request body:**

```json
{
  "monthly_income": 180000,
  "mobile_money_frequency": 52,
  "late_payments": 1,
  "account_age_months": 18,
  "user_id": "3fa85f64-..."
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `monthly_income` | integer | Yes | XAF, must be ≥ 0 |
| `mobile_money_frequency` | integer | Yes | Transactions per month |
| `late_payments` | integer | Yes | Count of late payments |
| `account_age_months` | integer | Yes | Months since account opened |
| `user_id` | UUID | No | If provided, saves a `RiskProfile` record. Analysts can only submit their own UUID. |

**Response `200 OK`:**

```json
{
  "risk_score": 81,
  "repayment_probability": 0.87,
  "recommended_loan": 270000,
  "explanation": "Stable income with consistent mobile money activity. Low late payment history indicates reliable repayment behavior.",
  "risk_profile_id": "abc-...",
  "user_id": "3fa85f64-..."
}
```

| Field | Range | Meaning |
|-------|-------|---------|
| `risk_score` | 0–100 | 0 = very high risk, 100 = very safe |
| `repayment_probability` | 0.0–1.0 | Probability of on-time repayment |
| `recommended_loan` | integer XAF | Suggested maximum loan amount |
| `risk_profile_id` | UUID or null | DB record ID if `user_id` was provided |

**Error `400`:** Validation errors for missing or invalid fields.

---

#### POST `/credit-score/analyze/batch/`

Batch credit scoring. Same format as `/transactions/batch/` — accepts JSON array or file upload. Each item must include the same fields as the single analyze endpoint.

**Response:** Batch results object with per-row `status` and `result`.

---

### 🚨 Fraud Detection

#### POST `/fraud/analyze/`

Analyze a transaction for fraud signals.

**Permissions:** Authenticated  
**AI Model:** Groq `llama-3.3-70b-versatile`

**Request body:**

```json
{
  "amount": 750000,
  "location": "Yaoundé",
  "device_change": true,
  "avg_amount": 90000,
  "transaction_id": "optional-uuid"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `amount` | decimal | Yes | Transaction amount in XAF |
| `location` | string | Yes | Transaction location |
| `device_change` | boolean | No | Default: `false` |
| `avg_amount` | decimal | No | User's average transaction (default: 150000) |
| `transaction_id` | UUID | No | If provided, saves/updates a `FraudAlert` record |
| `timestamp` | datetime | No | ISO 8601 |

**Response `200 OK`:**

```json
{
  "fraud_probability": 82,
  "urgency": "HIGH",
  "action": "BLOCK",
  "explanation": "Large transfer with simultaneous device change significantly deviates from typical behavior.",
  "indicators": [
    "Amount 8x above user average",
    "Device change detected",
    "Unusual transaction size"
  ],
  "alert_id": "uuid-or-null",
  "transaction_id": "uuid-or-null"
}
```

| Field | Values | Meaning |
|-------|--------|---------|
| `fraud_probability` | 0–100 | Likelihood of fraud |
| `urgency` | `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` | Alert severity |
| `action` | `ALLOW` / `FLAG` / `BLOCK` | Recommended action |
| `indicators` | string[] | Specific risk factors detected |

**Error responses:**

| Status | Condition |
|--------|-----------|
| `400` | Missing required `amount` field |
| `404` | Provided `transaction_id` not found |
| `403` | Analyst trying to analyze another user's transaction |

---

#### POST `/fraud/analyze/batch/`

Batch fraud detection. Same format as `/transactions/batch/`.

---

#### GET `/fraud/alerts/`

List fraud alerts. Admins see all; analysts see only their own. Limited to 50 most recent.

**Permissions:** Authenticated

**Response `200 OK`:**

```json
[
  {
    "id": "uuid",
    "transaction": "transaction-uuid",
    "transaction_amount": "750000.00",
    "transaction_location": "Yaoundé",
    "user_name": "Jean Pierre Mvondo",
    "fraud_probability": 82,
    "urgency": "HIGH",
    "explanation": "...",
    "indicators": ["Amount 8x above average", "Device change"],
    "action": "BLOCK",
    "created_at": "2026-05-15T10:30:00Z"
  }
]
```

---

### 📊 Analytics

#### GET `/analytics/dashboard/`

Retrieve all dashboard data: KPIs, chart data, recent transactions, and recent alerts.

**Permissions:** Authenticated  
**Scope:** Admins see platform-wide data; analysts see only their own.

**Response `200 OK`:**

```json
{
  "kpis": {
    "total_transactions": 147,
    "total_customers": 5,
    "avg_risk_score": 61.4,
    "active_fraud_alerts": 3,
    "high_risk_customers": 2,
    "low_risk_customers": 8
  },
  "charts": {
    "transaction_by_type": [
      {"type": "credit", "count": 62, "total": "7800000.00", "label": "credit", "value": 62},
      {"type": "debit", "count": 45, "total": "4100000.00", "label": "debit", "value": 45},
      {"type": "transfer", "count": 40, "total": "6200000.00", "label": "transfer", "value": 40}
    ],
    "transaction_by_method": [
      {"payment_method": "mobile_money", "count": 98, "label": "mobile_money", "value": 98},
      {"payment_method": "bank", "count": 32, "label": "bank", "value": 32},
      {"payment_method": "cash", "count": 17, "label": "cash", "value": 17}
    ],
    "fraud_by_urgency": [
      {"urgency": "LOW", "count": 5, "label": "LOW", "value": 5},
      {"urgency": "HIGH", "count": 3, "label": "HIGH", "value": 3}
    ],
    "risk_distribution": [
      {"label": "High Risk (0-39)", "value": 2, "color": "#EF4444"},
      {"label": "Medium Risk (40-69)", "value": 4, "color": "#F59E0B"},
      {"label": "Low Risk (70-100)", "value": 8, "color": "#22C55E"}
    ]
  },
  "recent_transactions": [...],
  "recent_alerts": [...]
}
```

Note: `transaction_by_type`, `transaction_by_method`, `fraud_by_urgency`, and `risk_distribution` are also returned at the top level (legacy format for backwards compatibility).

---

### 💡 AI Insights

#### POST `/ai/insights/`

Generate AI-powered executive insights for the portfolio.

**Permissions:** Authenticated  
**Behavior:** Reads live DB statistics automatically. You may optionally override with custom values in the request body.

**Request body (all optional):**

```json
{
  "total_transactions": 150,
  "avg_risk_score": 61,
  "active_alerts": 7,
  "total_loans": 12500000,
  "high_risk_count": 18
}
```

Send `{}` or an empty body to use live DB stats.

**Response `200 OK`:**

```json
{
  "summary": "Portfolio shows moderate risk distribution with growth opportunities in mobile money segments. Fraud detection systems are actively monitoring high-value transactions. Credit performance remains stable with improving repayment trends.",
  "recommendations": [
    "Increase credit limits for low-risk mobile money users",
    "Implement additional verification for device-change transactions",
    "Expand outreach to informal traders with 12+ months mobile money history"
  ],
  "risk_level": "MEDIUM",
  "opportunities": [
    "Underserved SME segment with strong mobile money activity",
    "Agricultural financing during harvest season"
  ]
}
```

| Field | Values | Notes |
|-------|--------|-------|
| `summary` | string | 3 sentences, executive overview |
| `recommendations` | string[] | 3 action items |
| `risk_level` | `LOW` / `MEDIUM` / `HIGH` | Portfolio risk classification |
| `opportunities` | string[] | Growth opportunities identified |

---

### 👤 User Risk Profiles

#### GET `/users/{user_id}/risk-profile/`

Retrieve a customer's complete profile: user info, most recent risk assessment, and last 20 transactions.

**Permissions:** Authenticated. Analysts can only access their own profile (`user_id` must match the token's user). Admins can access any user.

**Path parameter:** `user_id` — UUID of the target user

**Response `200 OK`:**

```json
{
  "user": {
    "id": "uuid",
    "full_name": "Jean Pierre Mvondo",
    "email": "jp.mvondo@demo.com",
    "role": "analyst"
  },
  "risk_profile": {
    "id": "uuid",
    "user": "uuid",
    "user_name": "Jean Pierre Mvondo",
    "risk_score": 81,
    "repayment_probability": 0.87,
    "recommended_loan": "250000.00",
    "ai_summary": "Stable income with consistent mobile money activity...",
    "created_at": "2026-05-15T10:30:00Z"
  },
  "recent_transactions": [...]
}
```

`risk_profile` is `null` if no credit analysis has been run for this user.

**Error responses:**

| Status | Condition |
|--------|-----------|
| `404` | User not found |
| `403` | Analyst accessing another user's profile |

---

### 📁 Dataset Templates

#### GET `/datasets/templates/{template_type}/{file_format}/`

Download a pre-filled template file for bulk imports.

**Permissions:** Authenticated  
**Path parameters:**
- `template_type`: `transactions` | `credit_score` | `fraud`  
- `file_format`: `json` | `csv` | `xlsx`

Returns a downloadable file with sample data matching the expected schema for batch endpoints.

---

## Error Format

All error responses follow this shape:

```json
{
  "error": "Human-readable message"
}
```

Or for DRF validation errors:

```json
{
  "field_name": ["Error message for this field."],
  "another_field": ["Another error."]
}
```

---

## Rate Limits

No rate limiting is currently implemented. The Groq API may impose its own limits — fallback deterministic logic activates automatically if Groq is unavailable.

---

## Postman Collection

A complete Postman test suite is included: `FinTrust_AI_Postman_Collection.json`

1. Import into Postman
2. Set `base_url` variable to your server URL
3. Run **🔐 Login (Admin)** first — tokens auto-save
4. Run any folder or use **🔁 Full Demo Flow** for end-to-end testing
