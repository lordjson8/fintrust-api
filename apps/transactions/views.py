from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Transaction
from .serializers import TransactionSerializer
from apps.ai_insights.datasets import load_dataset_entries
from apps.fraud_detection.models import FraudAlert
from apps.users.permissions import is_admin_user


class TransactionListCreateView(ListCreateAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        queryset = Transaction.objects.select_related('user')
        if not is_admin_user(self.request.user):
            queryset = queryset.filter(user=self.request.user)
        return queryset.order_by('-timestamp')[:50]

    def perform_create(self, serializer):
        requested_user = serializer.validated_data.get('user')
        if is_admin_user(self.request.user) and requested_user:
            serializer.save(user=requested_user)
            return

        serializer.save(user=self.request.user)

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


class TransactionBatchCreateView(APIView):
    def post(self, request):
        entries = load_dataset_entries(request)
        results = []
        success_count = 0

        for index, entry in enumerate(entries, start=1):
            data = dict(entry)
            if 'user_id' in data and 'user' not in data:
                # data['user'] = data.pop('user_id')
                data['user'] = request.user.id  # Override to current user for security


            serializer = TransactionSerializer(data=data)
            if not serializer.is_valid():
                results.append({
                    'row': index,
                    'status': 'failed',
                    'errors': serializer.errors,
                })
                continue

            requested_user = serializer.validated_data.get('user')
            save_kwargs = {}
            if is_admin_user(request.user) and requested_user:
                save_kwargs['user'] = requested_user
            else:
                save_kwargs['user'] = request.user

            transaction = serializer.save(**save_kwargs)
            success_count += 1
            results.append({
                'row': index,
                'status': 'success',
                'result': TransactionSerializer(transaction).data,
            })

        return Response({
            'total': len(entries),
            'succeeded': success_count,
            'failed': len(entries) - success_count,
            'results': results,
        })
