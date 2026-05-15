from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status
from .models import Transaction
from .serializers import TransactionSerializer
from apps.fraud_detection.models import FraudAlert


class TransactionListCreateView(ListCreateAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.select_related('user').all()[:50]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Attach fraud alert info to each transaction
        transaction_ids = [t.id for t in queryset]
        alerts = FraudAlert.objects.filter(
            transaction_id__in=transaction_ids
        ).values('transaction_id', 'fraud_probability', 'urgency', 'action')

        alert_map = {str(a['transaction_id']): a for a in alerts}

        data = serializer.data
        for txn in data:
            alert = alert_map.get(txn['id'])
            txn['fraud_alert'] = {
                'fraud_probability': alert['fraud_probability'],
                'urgency': alert['urgency'],
                'action': alert['action'],
            } if alert else None

        return Response(data)
