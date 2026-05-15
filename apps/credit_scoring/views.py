from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CreditScoreInputSerializer
from .models import RiskProfile
from apps.users.models import User
from apps.ai_insights.services.groq_service import safe_analyze_credit
from apps.users.permissions import is_admin_user


class CreditScoreAnalyzeView(APIView):
    def post(self, request):
        serializer = CreditScoreInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user_id = data.get('user_id')
        if not is_admin_user(request.user):
            if user_id and str(user_id) != str(request.user.id):
                return Response(
                    {'error': 'You do not have permission to score this user'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            user_id = request.user.id

        target_user = None
        if user_id:
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        ai_result = safe_analyze_credit(data)

        # Persist to DB if user_id provided
        risk_profile = None

        if target_user:
            risk_profile = RiskProfile.objects.create(
                user=target_user,
                risk_score=ai_result.get('risk_score', 0),
                repayment_probability=ai_result.get('repayment_probability', 0.0),
                recommended_loan=ai_result.get('recommended_loan', 0),
                ai_summary=ai_result.get('explanation', ''),
            )

        return Response({
            **ai_result,
            'risk_profile_id': str(risk_profile.id) if risk_profile else None,
        })
