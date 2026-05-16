from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from .serializers import FraudAnalyzeInputSerializer, FraudAlertSerializer
from .models import FraudAlert
from apps.transactions.models import Transaction
from apps.ai_insights.datasets import load_dataset_entries
from apps.ai_insights.services.groq_service import safe_analyze_fraud
from apps.users.permissions import is_admin_user


def analyze_fraud_entry(request_user, data):
    transaction_id = data.get('transaction_id')
    transaction = None
    if transaction_id:
        try:
            transaction = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist as exc:
            raise NotFound('Transaction not found') from exc

        if not is_admin_user(request_user) and transaction.user != request_user:
            raise PermissionDenied('You do not have permission to analyze this transaction')

    ai_result = safe_analyze_fraud(data)
    fraud_alert = None

    if transaction:
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

    return {
        **ai_result,
        'alert_id': str(fraud_alert.id) if fraud_alert else None,
        'transaction_id': str(transaction.id) if transaction else None,
    }


class FraudAnalyzeView(APIView):
    def post(self, request):
        serializer = FraudAnalyzeInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = {
            **serializer.validated_data,
            'language': request.data.get('language', 'en'),
        }
        return Response(analyze_fraud_entry(request.user, data))


class FraudBatchAnalyzeView(APIView):
    def post(self, request):
        entries = load_dataset_entries(request)
        results = []
        success_count = 0
        language = request.data.get('language', 'en')

        for index, entry in enumerate(entries, start=1):
            serializer = FraudAnalyzeInputSerializer(data=entry)
            if not serializer.is_valid():
                results.append({
                    'row': index,
                    'status': 'failed',
                    'errors': serializer.errors,
                })
                continue

            try:
                result = analyze_fraud_entry(request.user, {
                    **serializer.validated_data,
                    'language': language,
                })
            except (NotFound, PermissionDenied) as exc:
                results.append({
                    'row': index,
                    'status': 'failed',
                    'errors': {'detail': str(exc.detail)},
                })
                continue

            success_count += 1
            results.append({
                'row': index,
                'status': 'success',
                'result': result,
            })

        return Response({
            'total': len(entries),
            'succeeded': success_count,
            'failed': len(entries) - success_count,
            'results': results,
        })


class FraudAlertListView(APIView):
    def get(self, request):
        alerts = FraudAlert.objects.select_related(
            'transaction', 'transaction__user'
        )
        if not is_admin_user(request.user):
            alerts = alerts.filter(transaction__user=request.user)
        alerts = alerts.order_by('-created_at')[:50]
        return Response(FraudAlertSerializer(alerts, many=True).data)
