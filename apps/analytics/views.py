from rest_framework.views import APIView
from rest_framework.response import Response
from apps.transactions.models import Transaction
from apps.credit_scoring.models import RiskProfile
from apps.fraud_detection.models import FraudAlert
from apps.users.models import User
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import timedelta


class DashboardView(APIView):
    def get(self, request):
        now = timezone.now()
        last_30 = now - timedelta(days=30)

        # KPI Cards
        total_transactions = Transaction.objects.count()
        total_customers = User.objects.filter(role='analyst').count() + 4  # seed users
        avg_risk_score = RiskProfile.objects.aggregate(avg=Avg('risk_score'))['avg'] or 0
        active_fraud_alerts = FraudAlert.objects.exclude(action='ALLOW').count()
        high_risk_customers = RiskProfile.objects.filter(risk_score__lt=40).values('user').distinct().count()
        low_risk_customers = RiskProfile.objects.filter(risk_score__gte=70).values('user').distinct().count()

        # Transaction breakdown
        txn_by_type = list(
            Transaction.objects.values('type')
            .annotate(count=Count('id'), total=Sum('amount'))
            .order_by('type')
        )

        # Payment method breakdown
        txn_by_method = list(
            Transaction.objects.values('payment_method')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Fraud urgency distribution
        fraud_by_urgency = list(
            FraudAlert.objects.values('urgency')
            .annotate(count=Count('id'))
            .order_by('urgency')
        )

        # Risk score distribution (buckets)
        risk_distribution = [
            {'label': 'High Risk (0–39)', 'count': RiskProfile.objects.filter(risk_score__lt=40).count(), 'color': '#EF4444'},
            {'label': 'Medium Risk (40–69)', 'count': RiskProfile.objects.filter(risk_score__gte=40, risk_score__lt=70).count(), 'color': '#F59E0B'},
            {'label': 'Low Risk (70–100)', 'count': RiskProfile.objects.filter(risk_score__gte=70).count(), 'color': '#22C55E'},
        ]

        # Recent transactions (last 10)
        recent_transactions = list(
            Transaction.objects.select_related('user')
            .values('id', 'user__full_name', 'amount', 'type', 'payment_method', 'location', 'timestamp')
            .order_by('-timestamp')[:10]
        )

        # Recent fraud alerts (last 5)
        recent_alerts = list(
            FraudAlert.objects.select_related('transaction__user')
            .values(
                'id', 'fraud_probability', 'urgency', 'action', 'created_at',
                'transaction__amount', 'transaction__location', 'transaction__user__full_name'
            )
            .order_by('-created_at')[:5]
        )

        return Response({
            'kpis': {
                'total_transactions': total_transactions,
                'total_customers': total_customers,
                'avg_risk_score': round(avg_risk_score, 1),
                'active_fraud_alerts': active_fraud_alerts,
                'high_risk_customers': high_risk_customers,
                'low_risk_customers': low_risk_customers,
            },
            'charts': {
                'transaction_by_type': txn_by_type,
                'transaction_by_method': txn_by_method,
                'fraud_by_urgency': fraud_by_urgency,
                'risk_distribution': risk_distribution,
            },
            'recent_transactions': recent_transactions,
            'recent_alerts': recent_alerts,
        })
