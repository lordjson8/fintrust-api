from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CreditScoreInputSerializer, RiskProfileSerializer
from .models import RiskProfile
from apps.users.models import User
from apps.ai_insights.services.groq_service import safe_analyze_credit


class CreditScoreAnalyzeView(APIView):
    def post(self, request):
        serializer = CreditScoreInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        ai_result = safe_analyze_credit(data)

        # Persist to DB if user_id provided
        risk_profile = None
        user_id = data.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                risk_profile = RiskProfile.objects.create(
                    user=user,
                    risk_score=ai_result.get('risk_score', 0),
                    repayment_probability=ai_result.get('repayment_probability', 0.0),
                    recommended_loan=ai_result.get('recommended_loan', 0),
                    ai_summary=ai_result.get('explanation', ''),
                )
            except User.DoesNotExist:
                pass

        return Response({
            **ai_result,
            'risk_profile_id': str(risk_profile.id) if risk_profile else None,
        })
