from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from .serializers import CreditScoreInputSerializer
from .models import RiskProfile
from apps.users.models import User
from apps.ai_insights.datasets import load_dataset_entries
from apps.ai_insights.services.groq_service import safe_analyze_credit
from apps.users.permissions import is_admin_user


def analyze_credit_entry(request_user, data):
    user_id = data.get('user_id')
    if not is_admin_user(request_user):
        if user_id and str(user_id) != str(request_user.id):
            raise PermissionDenied('You do not have permission to score this user')
        user_id = request_user.id

    target_user = None
    if user_id:
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise NotFound('User not found') from exc

    ai_result = safe_analyze_credit(data)
    risk_profile = None

    if target_user:
        risk_profile = RiskProfile.objects.create(
            user=target_user,
            risk_score=ai_result.get('risk_score', 0),
            repayment_probability=ai_result.get('repayment_probability', 0.0),
            recommended_loan=ai_result.get('recommended_loan', 0),
            ai_summary=ai_result.get('explanation', ''),
        )

    return {
        **ai_result,
        'risk_profile_id': str(risk_profile.id) if risk_profile else None,
        'user_id': str(target_user.id) if target_user else None,
    }


class CreditScoreAnalyzeView(APIView):
    def post(self, request):
        serializer = CreditScoreInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(analyze_credit_entry(request.user, serializer.validated_data))


class CreditScoreBatchAnalyzeView(APIView):
    def post(self, request):
        entries = load_dataset_entries(request)
        results = []
        success_count = 0

        for index, entry in enumerate(entries, start=1):
            serializer = CreditScoreInputSerializer(data=entry)
            if not serializer.is_valid():
                results.append({
                    'row': index,
                    'status': 'failed',
                    'errors': serializer.errors,
                })
                continue

            try:
                result = analyze_credit_entry(request.user, serializer.validated_data)
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
