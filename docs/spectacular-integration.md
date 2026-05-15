# drf-spectacular Integration Guide

How to fully integrate OpenAPI documentation into the FinTrust AI Django backend.

---

## What's Already Installed

`drf-spectacular` is already in `requirements.txt` and `INSTALLED_APPS`, and the schema/Swagger/ReDoc routes are already wired in `config/urls.py`:

```python
# Already in config/urls.py (DEBUG mode only)
path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
```

---

## Step 1 — Replace SPECTACULAR_SETTINGS

Replace the minimal `SPECTACULAR_SETTINGS` in `config/settings.py` with the full config from `docs/spectacular_settings.py`. This adds:
- Rich API description with markdown
- Demo credentials table in the Swagger UI
- Risk score interpretation guide
- Server list (local + production)
- Tag definitions with descriptions
- Swagger UI persistence and filter settings

```python
# In config/settings.py, replace:
SPECTACULAR_SETTINGS = {
    'TITLE': 'Fintrust Project API',
    'DESCRIPTION': 'Your project description',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# With the full config from docs/spectacular_settings.py
```

---

## Step 2 — Add @extend_schema to Views

`docs/spectacular_views_annotated.py` contains complete drop-in replacements for all view files with full `@extend_schema` decorators.

Apply them to each app:

### `apps/authentication/views.py`

The `LoginView.post` and `RegisterView.post` methods get:
- Request body schema with field descriptions
- Response schemas (200, 400, 401)
- `OpenApiExample` entries showing demo credentials

### `apps/credit_scoring/views.py`

`CreditScoreAnalyzeView.post` gets:
- Full field documentation
- Risk score interpretation (0=high risk, 100=safe)
- Three examples: Jean Pierre (high score), Aminata (medium), Fatou (high risk)

### `apps/fraud_detection/views.py`

`FraudAnalyzeView.post` gets:
- Description of all fraud signals evaluated
- Three examples: high risk transfer, clean transaction, with transaction_id
- Urgency/action value tables

### `apps/ai_insights/views.py`

`AIInsightsView.post` gets:
- Explanation that empty body uses live DB stats
- Both empty and custom context examples

### `apps/analytics/views.py`

`DashboardView.get` gets a description of all returned data sections.

### `apps/users/views.py`

`UserRiskProfileView.get` gets path parameter documentation and permission notes.

---

## Step 3 — Tag Views in transactions/views.py

For the `TransactionListCreateView` (which extends `ListCreateAPIView`), add the `@extend_schema` decorator:

```python
from drf_spectacular.utils import extend_schema, OpenApiExample

class TransactionListCreateView(ListCreateAPIView):
    serializer_class = TransactionSerializer

    @extend_schema(
        tags=['Transactions'],
        summary='List transactions',
        description='Returns the 50 most recent transactions. Admins see all; analysts see their own.',
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=['Transactions'],
        summary='Create transaction',
        description='Create a new mobile money transaction. Analysts are force-assigned as the transaction owner.',
        examples=[
            OpenApiExample(
                'Mobile Money Credit',
                value={
                    'user': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                    'amount': 125000,
                    'type': 'credit',
                    'payment_method': 'mobile_money',
                    'location': 'Yaoundé',
                    'device_change': False,
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
```

---

## Step 4 — Verify the Schema

```bash
# Export the OpenAPI schema to a file
python manage.py spectacular --file schema.yml

# Or view it in browser
python manage.py runserver
# Open: http://localhost:8000/
```

The Swagger UI should show:
- All endpoints grouped by tag (Authentication, Transactions, Credit Scoring, etc.)
- Request/response schemas with field types and descriptions
- Example values that auto-populate when you click "Try it out"
- Authorization button (top right) — paste your Bearer token

---

## Step 5 — Using the Swagger UI for Demo

1. Open `http://localhost:8000/` in your browser
2. Click **Authorize** (top right) — enter `Bearer <your_token>`
3. The token persists in the browser session (`persistAuthorization: True`)
4. Expand any endpoint and click **Try it out → Execute**

This is a great way to demonstrate the API to judges interactively without needing Postman.

---

## Generating a Static Schema File

```bash
# YAML format (for sharing with API consumers)
python manage.py spectacular --file schema.yml --format openapi

# JSON format
python manage.py spectacular --file schema.json --format openapi-json
```

This file can be imported into:
- Postman (as an OpenAPI collection)
- Insomnia
- Any OpenAPI-compatible tool
- Frontend code generators (e.g., `openapi-typescript`)

---

## Making the Swagger UI Available in Production

The Swagger UI is gated behind `if settings.DEBUG`. To enable it in production for judges:

```python
# config/urls.py — remove the DEBUG check for demo:
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

> **Security note:** For a real production deployment, protect these routes with `IsAdminUser` permission. For a hackathon demo, public access is fine.
