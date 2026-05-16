from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .permissions import can_access_user
from apps.credit_scoring.models import RiskProfile
from apps.credit_scoring.serializers import RiskProfileSerializer
from apps.transactions.models import Transaction
from apps.transactions.serializers import TransactionSerializer
from apps.ai_insights.intelligence import build_customer_timeline, build_transaction_insights


class UserRiskProfileView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if not can_access_user(request.user, user):
            return Response(
                {'error': 'You do not have permission to access this user profile'},
                status=status.HTTP_403_FORBIDDEN,
            )

        risk_profile = RiskProfile.objects.filter(user=user).order_by('-created_at').first()
        transactions = Transaction.objects.filter(user=user).order_by('-timestamp')[:20]
        transaction_history = Transaction.objects.filter(user=user).order_by('-timestamp')[:100]
        language = request.query_params.get('language') or request.headers.get('Accept-Language', 'en')

        return Response({
            'user': {
                'id': str(user.id),
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role,
            },
            'risk_profile': RiskProfileSerializer(risk_profile).data if risk_profile else None,
            'recent_transactions': TransactionSerializer(transactions, many=True).data,
            'transaction_insights': build_transaction_insights(transaction_history, language),
            'timeline': build_customer_timeline(user, language=language),
        })
