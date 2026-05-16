from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.transactions.models import Transaction
from apps.transactions.serializers import TransactionSerializer
from apps.credit_scoring.models import RiskProfile
from apps.credit_scoring.serializers import CreditScoreInputSerializer
from apps.fraud_detection.models import FraudAlert
from apps.fraud_detection.serializers import FraudAnalyzeInputSerializer
from apps.ai_insights.datasets import load_dataset_entries
from apps.ai_insights.intelligence import build_dataset_quality_report
from apps.ai_insights.services.groq_service import safe_analyze_insights
from apps.users.permissions import is_admin_user
from django.db.models import Avg


class AIInsightsView(APIView):
    def post(self, request):
        transactions = Transaction.objects.all()
        risk_profiles = RiskProfile.objects.all()
        fraud_alerts = FraudAlert.objects.all()

        if not is_admin_user(request.user):
            transactions = transactions.filter(user=request.user)
            risk_profiles = risk_profiles.filter(user=request.user)
            fraud_alerts = fraud_alerts.filter(transaction__user=request.user)

        # Gather portfolio stats for context
        data = {
            'total_transactions': transactions.count(),
            'avg_risk_score': risk_profiles.aggregate(avg=Avg('risk_score'))['avg'] or 0,
            'active_alerts': fraud_alerts.exclude(action='ALLOW').count(),
            'total_loans': 0,  # Can add LoanRequest model later
            'high_risk_count': risk_profiles.filter(risk_score__lt=40).count(),
        }
        # Allow override from request body
        data.update(request.data)
        result = safe_analyze_insights(data)
        return Response(result)


class DatasetQualityView(APIView):
    serializer_map = {
        'transactions': (
            TransactionSerializer,
            ['amount', 'type', 'payment_method', 'location'],
        ),
        'credit': (
            CreditScoreInputSerializer,
            ['monthly_income', 'mobile_money_frequency', 'late_payments', 'account_age_months'],
        ),
        'fraud': (
            FraudAnalyzeInputSerializer,
            ['amount', 'location', 'device_change'],
        ),
    }

    def post(self, request, dataset_type):
        config = self.serializer_map.get(dataset_type)
        if not config:
            return Response(
                {'error': 'Unsupported dataset type. Use transactions, credit, or fraud.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer_class, required_fields = config
        entries = load_dataset_entries(request)
        language = request.data.get('language') or request.headers.get('Accept-Language', 'en')
        return Response(build_dataset_quality_report(entries, serializer_class, required_fields, language))
