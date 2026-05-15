# Frontend Architecture Guide — FinTrust AI

Next.js 14 + TypeScript + Tailwind CSS + React Query frontend guide.

---

## Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| Next.js | 14.2 | App Router, SSR, routing |
| TypeScript | 5 | Type safety |
| Tailwind CSS | 3.4 | Styling (no CSS modules, no inline styles) |
| React Query | 5 | Server state, caching, mutations |
| Axios | 1.7 | HTTP client with JWT interceptors |
| Zustand | 4.5 | Client auth state (persisted) |
| Recharts | 2.12 | Charts and data visualization |
| react-hot-toast | 2.4 | Toast notifications |
| lucide-react | 0.427 | Icons |

---

## Directory Structure

```
src/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # Root layout (fonts, providers)
│   ├── globals.css               # Global styles, Tailwind directives
│   ├── page.tsx                  # Redirects to /dashboard
│   ├── login/
│   │   └── page.tsx              # Login page (no AppShell)
│   ├── dashboard/
│   │   └── page.tsx              # Main dashboard
│   ├── transactions/
│   │   └── page.tsx              # Transaction list + create form
│   ├── risk-analysis/
│   │   └── page.tsx              # Credit scoring + fraud detection forms
│   ├── alerts/
│   │   └── page.tsx              # Fraud alert list
│   ├── ai-insights/
│   │   └── page.tsx              # AI portfolio insights
│   ├── analytics/
│   │   └── page.tsx              # Charts and trends
│   └── customers/
│       └── [id]/
│           └── page.tsx          # Customer risk profile
│
├── components/
│   ├── layout/
│   │   ├── Providers.tsx         # React Query + Toast providers
│   │   ├── AppShell.tsx          # Auth guard + Sidebar + Topbar wrapper
│   │   ├── Sidebar.tsx           # Collapsible nav sidebar
│   │   └── Topbar.tsx            # Page title + search + alerts bell
│   ├── shared/
│   │   ├── KPICard.tsx           # Metric card with icon + trend
│   │   ├── RiskScoreBadge.tsx    # Color-coded 0–100 score chip
│   │   ├── FraudBadge.tsx        # Urgency level chip
│   │   ├── TransactionTable.tsx  # Paginated transaction list
│   │   ├── LoadingSkeleton.tsx   # Shimmer skeleton variants
│   │   ├── EmptyState.tsx        # No data placeholder
│   │   └── ErrorState.tsx        # API error display
│   └── charts/
│       ├── RiskDistributionChart.tsx   # Donut chart
│       ├── TransactionVolumeChart.tsx  # Bar chart
│       └── FraudUrgencyChart.tsx       # Bar/donut chart
│
├── hooks/
│   └── queries.ts                # All React Query hooks
│
├── lib/
│   ├── axios.ts                  # Axios instance + JWT interceptor
│   ├── api.ts                    # API service functions
│   └── utils.ts                  # cn(), formatCurrency(), getRiskColor(), etc.
│
├── store/
│   └── auth.ts                   # Zustand auth store (persisted to localStorage)
│
└── types/
    └── index.ts                  # All TypeScript interfaces
```

---

## Authentication Flow

1. User lands on any protected route → `AppShell` checks `isAuthenticated` from Zustand
2. If not authenticated → redirect to `/login`
3. On login → `authApi.login()` → store tokens in Zustand + localStorage
4. All subsequent requests → Axios interceptor reads `access_token` from localStorage and injects `Authorization: Bearer <token>` header
5. On 401 response → Axios interceptor attempts token refresh using `refresh_token`
6. If refresh fails → clear auth state → redirect to `/login`

```
[Request] → axios.interceptors.request
              → inject Authorization header
              ↓
[Response 401] → axios.interceptors.response
                  → call /auth/refresh/
                  → if success: retry original request with new token
                  → if fail: clearAuth() + redirect /login
```

---

## Data Fetching Pattern

All data fetching goes through **React Query hooks** in `src/hooks/queries.ts`. Components never call `fetch` or `axios` directly.

### Query hooks (read data)

```typescript
// In a component:
const { data, isLoading, error } = useDashboard()
const { data: transactions } = useTransactions()
```

### Mutation hooks (write data)

```typescript
const createTransaction = useCreateTransaction()

const handleSubmit = async (values) => {
  await createTransaction.mutateAsync(values)
  toast.success('Transaction created')
}
```

### Cache invalidation

After mutations, the relevant query keys are invalidated automatically:

```typescript
// useCreateTransaction:
onSuccess: () => {
  qc.invalidateQueries({ queryKey: QK.transactions })
  qc.invalidateQueries({ queryKey: QK.dashboard })
}
```

### Query keys

All query keys are defined in `QK` in `hooks/queries.ts`:

```typescript
export const QK = {
  transactions: ['transactions'],
  dashboard: ['dashboard'],
  fraudAlerts: ['fraud-alerts'],
  aiInsights: ['ai-insights'],
  riskProfile: (id: string) => ['risk-profile', id],
}
```

---

## Styling Rules

1. **Tailwind only** — no inline styles, no CSS modules
2. **Design tokens** defined in `tailwind.config.js`:
   - `bg-background` → `#020617` (page background)
   - `bg-surface` → `#0F172A` (cards)
   - `border-border` → `#1E293B`
   - `text-primary` → `#0EA5E9`
   - `text-text-primary` → `#F1F5F9`
   - `text-text-muted` → `#94A3B8`
   - `text-success` → `#22C55E`
   - `text-warning` → `#F59E0B`
   - `text-danger` → `#EF4444`
3. **`cn()` utility** for conditional class merging (clsx + tailwind-merge)
4. **No blank loading states** — every data fetch shows a `LoadingSkeleton`
5. **Stagger animations** — use `.stagger` class on containers to animate children in sequence

---

## Color-Coded Risk System

Risk scores (0–100) are consistently colored across all components using utilities in `lib/utils.ts`:

```typescript
getRiskLevel(score)  // 'low' | 'medium' | 'high'
getRiskColor(score)  // 'text-success' | 'text-warning' | 'text-danger'
getRiskBg(score)     // Tailwind bg + text + border combo string

getUrgencyColor(urgency)  // FraudUrgency → Tailwind class string
getActionColor(action)    // 'ALLOW'|'FLAG'|'BLOCK' → text color class
```

---

## Key Components

### AppShell

Wraps every authenticated page. Renders `Sidebar` + `Topbar` + `<main>`.
Auth guard: redirects to `/login` if `!isAuthenticated`.

### KPICard

```tsx
<KPICard
  title="Active Fraud Alerts"
  value={3}
  icon={<ShieldAlert />}
  trend={{ value: 2, direction: 'up', isGood: false }}
  color="danger"
/>
```

### RiskScoreBadge

```tsx
<RiskScoreBadge score={81} />
// Renders: green chip "81" with "Low Risk" label
```

### FraudBadge

```tsx
<FraudBadge urgency="HIGH" />
// Renders: red "HIGH" chip
```

### LoadingSkeleton

```tsx
<LoadingSkeleton variant="card" />     // KPI card skeleton
<LoadingSkeleton variant="table" />    // Table row skeletons
<LoadingSkeleton variant="chart" />    // Chart area skeleton
```

---

## Page Layout Pattern

Every authenticated page follows this pattern:

```tsx
export default function SomePage() {
  return (
    <AppShell>
      <div className="space-y-6">
        {/* Page header */}
        <div>
          <h2 className="text-2xl font-bold text-text-primary">Page Title</h2>
          <p className="text-text-muted text-sm mt-1">Description</p>
        </div>

        {/* Content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ... */}
        </div>
      </div>
    </AppShell>
  )
}
```

---

## Adding a New Page

1. Create `src/app/new-page/page.tsx`
2. Wrap content in `<AppShell>`
3. Add the route to `Sidebar.tsx` `navItems` array
4. Add the title to `Topbar.tsx` `pageTitles` map
5. Add any new API calls to `lib/api.ts`
6. Add React Query hooks to `hooks/queries.ts`

---

## Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

The `NEXT_PUBLIC_` prefix makes this available in browser-side code. Never put secrets in `NEXT_PUBLIC_` variables.

---

## Build and Deploy

```bash
npm run dev      # Development server (localhost:3000)
npm run build    # Production build
npm run start    # Start production server
npm run lint     # ESLint check
```

Vercel auto-detects Next.js and handles builds. Just push to main branch.
