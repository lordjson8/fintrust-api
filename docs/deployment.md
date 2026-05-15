# Deployment Guide — FinTrust AI

Step-by-step guide to deploy the backend on **Railway** and the frontend on **Vercel**.

---

## Backend — Railway

### Prerequisites

- [Railway account](https://railway.app) (free tier works)
- Groq API key from [console.groq.com](https://console.groq.com)

### Step 1 — Create Railway Project

1. Go to [railway.app/new](https://railway.app/new)
2. Click **Deploy from GitHub repo**
3. Select your repository

If your Django project is in a subfolder (e.g., `backend/`), set the root directory in Railway settings.

### Step 2 — Add PostgreSQL

1. In your Railway project, click **+ New Service**
2. Select **Database → PostgreSQL**
3. Railway automatically sets the `DATABASE_URL` environment variable

### Step 3 — Configure Environment Variables

In **Railway → Your Service → Variables**, add:

```
SECRET_KEY=your-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app
DATABASE_URL=<auto-set by Railway PostgreSQL>
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
CORS_ALLOW_ALL_ORIGINS=False
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Important:** Set `DEBUG=False` in production. This disables the Swagger UI and enables security features.

> **Important:** Update `CORS_ALLOWED_ORIGINS` once you have your Vercel URL.

### Step 4 — Configure Start Command

Railway uses the `Dockerfile` automatically. The CMD in the Dockerfile is:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

This is correct for production.

### Step 5 — Run Migrations and Seed

After the first deploy, open Railway's **Shell** or use the CLI:

```bash
# Run migrations
python manage.py migrate

# Seed demo data
python manage.py seed_demo

# Create superuser (optional, in addition to seeded admin)
python manage.py createsuperuser
```

Or add a Railway deploy hook:

```bash
python manage.py migrate && python manage.py seed_demo
```

### Step 6 — Verify

Your backend is live at: `https://your-app.railway.app`

Test it:
```bash
curl https://your-app.railway.app/api/v1/auth/login/ \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@fintrust.ai", "password": "admin1234"}'
```

---

## Frontend — Vercel

### Prerequisites

- [Vercel account](https://vercel.com) (free tier works)
- Deployed Railway backend URL

### Step 1 — Import Project

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click **Import Git Repository**
3. Select your repository
4. Set **Root Directory** to `frontend/` (or wherever your Next.js app lives)

### Step 2 — Configure Environment Variables

In **Vercel → Project Settings → Environment Variables**:

```
NEXT_PUBLIC_API_URL=https://your-app.railway.app/api/v1
```

### Step 3 — Deploy Settings

Vercel auto-detects Next.js. Default settings work:

| Setting | Value |
|---------|-------|
| Framework | Next.js |
| Build Command | `npm run build` |
| Output Directory | `.next` |
| Install Command | `npm install` |

### Step 4 — Deploy

Click **Deploy**. Vercel builds and deploys automatically.

Your frontend is live at: `https://your-app.vercel.app`

### Step 5 — Update CORS on Railway

Go back to Railway → Variables and update:

```
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
```

Redeploy (or Railway will pick it up automatically).

---

## Environment Variables Reference

### Backend (Railway)

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `SECRET_KEY` | Yes | insecure default | Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | Yes | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | Yes | `*` | Set to your Railway domain in production |
| `DATABASE_URL` | Yes | SQLite | Auto-set by Railway PostgreSQL add-on |
| `CORS_ALLOWED_ORIGINS` | Yes | localhost:3000 | Comma-separated list of frontend URLs |
| `CORS_ALLOW_ALL_ORIGINS` | No | `True` | Set `False` in production |
| `GROQ_API_KEY` | Yes | empty | From console.groq.com |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model identifier |

### Frontend (Vercel)

| Variable | Required | Notes |
|----------|----------|-------|
| `NEXT_PUBLIC_API_URL` | Yes | Full URL including `/api/v1` |

---

## Dockerfile Reference

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
```

Static files are collected at build time using WhiteNoise (`STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`), so no separate static file hosting is needed.

---

## Connecting Postman to Production

Update the `base_url` collection variable in Postman:

```
base_url = https://your-app.railway.app/api/v1
```

Then run the Full Demo Flow — it works identically against production.

---

## Health Check

Railway can auto-restart unhealthy services. Add a health check endpoint by adding to `config/api_urls.py`:

```python
from django.http import JsonResponse
from django.views import View

class HealthCheckView(View):
    def get(self, request):
        return JsonResponse({"status": "ok", "version": "1.0.0"})

# In urlpatterns:
path('health/', HealthCheckView.as_view(), name='health'),
```

Set the Railway health check path to `/api/v1/health/`.

---

## Troubleshooting

**`CSRF verification failed` on POST requests:**  
DRF uses JWT, not CSRF cookies. This shouldn't occur. Verify `Content-Type: application/json` is set on all requests.

**`CORS error` in browser:**  
Ensure `CORS_ALLOWED_ORIGINS` includes your exact Vercel URL (no trailing slash). If testing locally, add `http://localhost:3000`.

**`502 Bad Gateway` on Railway:**  
Check logs for migration errors. Run `python manage.py migrate` from the Railway shell.

**Groq API timeout:**  
The fallback logic activates automatically. Check that `GROQ_API_KEY` is set correctly in Railway variables.

**`collectstatic` failure at build:**  
Ensure `DJANGO_SETTINGS_MODULE` is set (it defaults to `config.settings`). WhiteNoise requires `STATIC_ROOT` to be set, which it is in `settings.py`.
