from rest_framework import serializers
from .models import FraudAlert


class FraudAlertSerializer(serializers.ModelSerializer):
    transaction_amount = serializers.DecimalField(
        source='transaction.amount', max_digits=12, decimal_places=2, read_only=True
    )
    transaction_location = serializers.CharField(source='transaction.location', read_only=True)
    user_name = serializers.CharField(source='transaction.user.full_name', read_only=True)

    class Meta:
        model = FraudAlert
        fields = [
            'id', 'transaction', 'transaction_amount', 'transaction_location',
            'user_name', 'fraud_probability', 'urgency', 'explanation',
            'indicators', 'action', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class FraudAnalyzeInputSerializer(serializers.Serializer):
    transaction_id = serializers.UUIDField(required=False)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    location = serializers.CharField(max_length=100)
    device_change = serializers.BooleanField(default=False)
    timestamp = serializers.DateTimeField(required=False)
    avg_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=150000)
