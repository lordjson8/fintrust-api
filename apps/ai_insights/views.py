from rest_framework.views import APIView
from rest_framework.response import Response
from apps.transactions.models import Transaction
from apps.credit_scoring.models import RiskProfile
from apps.fraud_detection.models import FraudAlert
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
