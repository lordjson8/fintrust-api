# FinTrust AI — Credit Intelligence Platform

> AI-powered credit scoring and fraud detection for African financial institutions, built on mobile money behavioral data.

[![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.15-red)](https://www.django-rest-framework.org)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-orange)](https://groq.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Railway-336791?logo=postgresql)](https://railway.app)

---

## Overview

FinTrust AI solves the financial inclusion gap in Africa. Traditional credit scoring requires salary slips, collateral, and formal bank history — documents most citizens don't have. FinTrust replaces these with **behavioral intelligence**: mobile money frequency, repayment patterns, income irregularity, and fraud signals.

An analyst logs in, submits a customer's financial profile, and receives in seconds:
- A **risk score** (0–100) with AI explanation
- A **fraud probability** with action recommendation (ALLOW / FLAG / BLOCK)
- A **recommended loan amount** in XAF
- **Portfolio-wide insights** from AI across all customers

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Next.js 14 Frontend               │
│  (TypeScript · Tailwind · shadcn/ui · React Query)  │
└──────────────────────┬──────────────────────────────┘
                       │ REST / JWT
┌──────────────────────▼──────────────────────────────┐
│               Django 5 + DRF Backend                 │
│    apps: auth · users · transactions · analytics    │
│           credit_scoring · fraud_detection          │
│                   ai_insights                       │
└─────────┬─────────────────────────┬────────────────┘
          │                         │
┌─────────▼──────────┐   ┌──────────▼──────────┐
│   PostgreSQL        │   │   Groq API           │
│   (Railway)         │   │   llama-3.3-70b      │
└────────────────────┘   └─────────────────────┘
```

**Tech stack:**

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.0.4, DRF 3.15.1, SimpleJWT 5.3.1 |
| Frontend | React.js ,Tanstack Router, TypeScript, Tailwind CSS, shadcn/ui |
| AI | Groq API — `llama-3.3-70b-versatile` |
| Database | PostgreSQL (Railway) |
| Auth | JWT (Bearer tokens, 8h access / 7d refresh) |
| API Docs | drf-spectacular (OpenAPI 3.0 + Swagger UI) |
| Deployment | Railway (backend) · Vercel (frontend) |

---

## Repository Structure

```
fintrust/
├── backend/                  # Django project root
│   ├── apps/
│   │   ├── authentication/   # Login, Register, Token Refresh
│   │   ├── users/            # User model, permissions, risk profile view
│   │   │   └── management/commands/seed_demo.py
│   │   ├── transactions/     # Transaction model, CRUD, batch import
│   │   ├── credit_scoring/   # RiskProfile model, AI credit analysis
│   │   ├── fraud_detection/  # FraudAlert model, AI fraud analysis
│   │   ├── ai_insights/      # Portfolio AI insights (Groq)
│   │   │   └── services/groq_service.py
│   │   └── analytics/        # Dashboard KPIs and chart data
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── api_urls.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                 # Next.js 14 project
│   ├── src/
│   │   ├── app/              # App Router pages
│   │   ├── components/       # Shared UI components
│   │   ├── hooks/            # React Query hooks
│   │   ├── lib/              # axios instance, API services, utils
│   │   ├── store/            # Zustand auth store
│   │   └── types/            # TypeScript types
│   └── ...
│
├── docs/                     # Extended documentation
│   ├── api-reference.md      # Full API reference
│   ├── data-models.md        # Database schema and models
│   ├── ai-system.md          # Groq integration and prompts
│   ├── frontend-guide.md     # Frontend architecture guide
│   ├── deployment.md         # Railway + Vercel deployment
│   └── demo-guide.md         # Hackathon demo walkthrough
│
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (local or Railway)
- Groq API key → [console.groq.com](https://console.groq.com)

### Backend

```bash
# 1. Clone and enter project
git clone https://github.com/your-org/fintrust-ai
cd fintrust-ai/backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# → Edit .env with your DATABASE_URL and GROQ_API_KEY

# 5. Run migrations
python manage.py migrate

# 6. Seed demo data (creates 5 users + 80 transactions + risk profiles)
python manage.py seed_demo

# 7. Start development server
python manage.py runserver
```

Backend runs at `http://localhost:8000`
Swagger UI at `http://localhost:8000/` (DEBUG mode only)



## API Overview

Base URL: `http://localhost:8000/api/v1/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login/` | Login, returns JWT tokens |
| POST | `/auth/register/` | Register new analyst |
| POST | `/auth/refresh/` | Refresh access token |
| GET | `/transactions/` | List transactions |
| POST | `/transactions/` | Create transaction |
| POST | `/transactions/batch/` | Batch import (JSON/CSV/XLSX) |
| POST | `/credit-score/analyze/` | AI credit risk analysis |
| POST | `/credit-score/analyze/batch/` | Batch credit scoring |
| POST | `/fraud/analyze/` | AI fraud detection |
| POST | `/fraud/analyze/batch/` | Batch fraud detection |
| GET | `/fraud/alerts/` | List fraud alerts |
| POST | `/ai/insights/` | Portfolio AI insights |
| GET | `/analytics/dashboard/` | Dashboard KPIs + charts |
| GET | `/users/{id}/risk-profile/` | Customer risk profile |

Full API reference → [`docs/api-reference.md`](docs/api-reference.md)

---

## Key Features

### AI Credit Scoring
Analyzes mobile money behavior (income, frequency, late payments, account age) via Groq's Llama 3.3 70B. Returns a 0–100 risk score, repayment probability, loan recommendation, and AI explanation. Falls back to deterministic scoring if the Groq API is unavailable.

### Fraud Detection
Real-time transaction fraud analysis using amount deviation, location, device change signals. Returns fraud probability (0–100), urgency level (LOW/MEDIUM/HIGH/CRITICAL), and recommended action (ALLOW/FLAG/BLOCK).

### Portfolio Insights
AI reads live database statistics and generates executive-level summary, recommendations, and identified opportunities for the loan portfolio.

### Batch Processing
All AI endpoints support batch mode — upload a CSV/XLSX dataset and get bulk analysis results. Useful for seeding and demo scenarios.

### Role-Based Access
- **Admin**: sees all users, all transactions, all alerts, all analytics
- **Analyst**: sees only their own transactions, risk profiles, and alerts

---

## Environment Variables

```bash
# Django backend (.env)
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=*
DATABASE_URL=postgresql://user:pass@host:5432/db
CORS_ALLOWED_ORIGINS=http://localhost:3000
CORS_ALLOW_ALL_ORIGINS=True
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile

# Next.js frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Deployment

See [`docs/deployment.md`](docs/deployment.md) for full Railway + Vercel deployment guide.

**Quick deploy summary:**
1. Push backend to Railway → set env vars → runs on Dockerfile
2. Push frontend to Vercel → set `NEXT_PUBLIC_API_URL` to Railway URL
3. Update `CORS_ALLOWED_ORIGINS` in Railway with the Vercel domain

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [`docs/api-reference.md`](docs/api-reference.md) | Every endpoint with request/response examples |
| [`docs/data-models.md`](docs/data-models.md) | Database schema, model fields, relationships |
| [`docs/ai-system.md`](docs/ai-system.md) | Groq integration, prompts, fallback logic |
| [`docs/frontend-guide.md`](docs/frontend-guide.md) | Frontend architecture, components, patterns |
| [`docs/deployment.md`](docs/deployment.md) | Railway + Vercel step-by-step deployment |
| [`docs/demo-guide.md`](docs/demo-guide.md) | Full hackathon demo walkthrough script |

---

## Testing

```bash
# Run backend tests
cd backend
python manage.py test apps.users

# Run Postman collection (full API test suite)
# Import FinTrust_AI_Postman_Collection.json into Postman
# Run "🔐 Login (Admin)" first — tokens auto-save
# Then run any other folder or the "🔁 Full Demo Flow"
```

---

## License

MIT — built for the FinTrust AI Hackathon.
