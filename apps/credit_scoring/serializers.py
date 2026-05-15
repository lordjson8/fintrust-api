from rest_framework import serializers
from .models import RiskProfile


class RiskProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = RiskProfile
        fields = [
            'id', 'user', 'user_name', 'risk_score', 'repayment_probability',
            'recommended_loan', 'ai_summary', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CreditScoreInputSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=False)
    monthly_income = serializers.IntegerField(min_value=0)
    mobile_money_frequency = serializers.IntegerField(min_value=0)
    late_payments = serializers.IntegerField(min_value=0)
    account_age_months = serializers.IntegerField(min_value=0)
