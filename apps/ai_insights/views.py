from rest_framework.views import APIView
from rest_framework.response import Response
from apps.transactions.models import Transaction
from apps.credit_scoring.models import RiskProfile
from apps.fraud_detection.models import FraudAlert
from apps.ai_insights.services.groq_service import safe_analyze_insights
from django.db.models import Avg, Count, Sum


class AIInsightsView(APIView):
    def post(self, request):
        # Gather portfolio stats for context
        data = {
            'total_transactions': Transaction.objects.count(),
            'avg_risk_score': RiskProfile.objects.aggregate(avg=Avg('risk_score'))['avg'] or 0,
            'active_alerts': FraudAlert.objects.exclude(action='ALLOW').count(),
            'total_loans': 0,  # Can add LoanRequest model later
            'high_risk_count': RiskProfile.objects.filter(risk_score__lt=40).count(),
        }
        # Allow override from request body
        data.update(request.data)
        result = safe_analyze_insights(data)
        return Response(result)
