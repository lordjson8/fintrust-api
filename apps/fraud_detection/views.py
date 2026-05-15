from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FraudAnalyzeInputSerializer, FraudAlertSerializer
from .models import FraudAlert
from apps.transactions.models import Transaction
from apps.ai_insights.services.groq_service import safe_analyze_fraud


class FraudAnalyzeView(APIView):
    def post(self, request):
        serializer = FraudAnalyzeInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        ai_result = safe_analyze_fraud(data)

        # Persist to DB if transaction_id provided
        fraud_alert = None
        transaction_id = data.get('transaction_id')
        if transaction_id:
            try:
                transaction = Transaction.objects.get(id=transaction_id)
                fraud_alert, _ = FraudAlert.objects.update_or_create(
                    transaction=transaction,
                    defaults={
                        'fraud_probability': ai_result.get('fraud_probability', 0),
                        'urgency': ai_result.get('urgency', 'LOW'),
                        'explanation': ai_result.get('explanation', ''),
                        'indicators': ai_result.get('indicators', []),
                        'action': ai_result.get('action', 'ALLOW'),
                    }
                )
            except Transaction.DoesNotExist:
                pass

        return Response({
            **ai_result,
            'alert_id': str(fraud_alert.id) if fraud_alert else None,
        })


class FraudAlertListView(APIView):
    def get(self, request):
        alerts = FraudAlert.objects.select_related(
            'transaction', 'transaction__user'
        ).all()[:50]
        return Response(FraudAlertSerializer(alerts, many=True).data)
