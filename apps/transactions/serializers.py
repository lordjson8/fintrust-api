from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'user_name', 'amount', 'type',
            'payment_method', 'location', 'timestamp', 'device_change'
        ]
        read_only_fields = ['id', 'timestamp']
        extra_kwargs = {'user': {'required': False}}
