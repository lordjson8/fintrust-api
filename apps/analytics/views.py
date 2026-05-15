from rest_framework.views import APIView
from rest_framework.response import Response
from apps.transactions.models import Transaction
from apps.credit_scoring.models import RiskProfile
from apps.fraud_detection.models import FraudAlert
from apps.users.models import User
from apps.users.permissions import is_admin_user
from django.db.models import Avg, Count, Sum


class DashboardView(APIView):
    def get(self, request):
        admin_view = is_admin_user(request.user)

        transactions = Transaction.objects.all()
        risk_profiles = RiskProfile.objects.all()
        fraud_alerts = FraudAlert.objects.select_related('transaction__user')
        users = User.objects.all()

        if not admin_view:
            transactions = transactions.filter(user=request.user)
            risk_profiles = risk_profiles.filter(user=request.user)
            fraud_alerts = fraud_alerts.filter(transaction__user=request.user)
            users = users.filter(id=request.user.id)

        # KPI Cards
        total_transactions = transactions.count()
        total_customers = users.filter(role='analyst').count()
        avg_risk_score = risk_profiles.aggregate(avg=Avg('risk_score'))['avg'] or 0
        active_fraud_alerts = fraud_alerts.exclude(action='ALLOW').count()
        high_risk_customers = risk_profiles.filter(risk_score__lt=40).values('user').distinct().count()
        low_risk_customers = risk_profiles.filter(risk_score__gte=70).values('user').distinct().count()

        # Transaction breakdown
        txn_by_type = list(
            transactions.values('type')
            .annotate(count=Count('id'), total=Sum('amount'))
            .order_by('type')
        )

        # Payment method breakdown
        txn_by_method = list(
            transactions.values('payment_method')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Fraud urgency distribution
        fraud_by_urgency = list(
            fraud_alerts.values('urgency')
            .annotate(count=Count('id'))
            .order_by('urgency')
        )

        # Risk score distribution (buckets)
        risk_distribution = [
            {'label': 'High Risk (0-39)', 'count': risk_profiles.filter(risk_score__lt=40).count(), 'color': '#EF4444'},
            {'label': 'Medium Risk (40-69)', 'count': risk_profiles.filter(risk_score__gte=40, risk_score__lt=70).count(), 'color': '#F59E0B'},
            {'label': 'Low Risk (70-100)', 'count': risk_profiles.filter(risk_score__gte=70).count(), 'color': '#22C55E'},
        ]

        # Recent transactions (last 10)
        recent_transactions = list(
            transactions.select_related('user')
            .values('id', 'user__full_name', 'amount', 'type', 'payment_method', 'location', 'timestamp')
            .order_by('-timestamp')[:10]
        )

        # Recent fraud alerts (last 5)
        recent_alerts = list(
            fraud_alerts.values(
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
