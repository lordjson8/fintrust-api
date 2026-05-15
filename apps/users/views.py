from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from apps.credit_scoring.models import RiskProfile
from apps.credit_scoring.serializers import RiskProfileSerializer
from apps.transactions.models import Transaction
from apps.transactions.serializers import TransactionSerializer


class UserRiskProfileView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        risk_profile = RiskProfile.objects.filter(user=user).order_by('-created_at').first()
        transactions = Transaction.objects.filter(user=user).order_by('-timestamp')[:20]

        return Response({
            'user': {
                'id': str(user.id),
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role,
            },
            'risk_profile': RiskProfileSerializer(risk_profile).data if risk_profile else None,
            'recent_transactions': TransactionSerializer(transactions, many=True).data,
        })
