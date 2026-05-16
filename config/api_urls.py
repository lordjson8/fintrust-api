from django.urls import path
from apps.authentication.views import LoginView, RegisterView, RefreshView
from apps.transactions.views import TransactionBatchCreateView, TransactionListCreateView
from apps.credit_scoring.views import CreditScoreAnalyzeView, CreditScoreBatchAnalyzeView
from apps.fraud_detection.views import FraudAlertListView, FraudAnalyzeView, FraudBatchAnalyzeView
from apps.ai_insights.views import AIInsightsView, DatasetQualityView
from apps.ai_insights.templates import DatasetTemplateDownloadView
from apps.analytics.views import DashboardView
from apps.users.views import UserRiskProfileView

urlpatterns = [
    # Auth
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/refresh/', RefreshView.as_view(), name='refresh'),

    # Transactions
    path('transactions/', TransactionListCreateView.as_view(), name='transactions'),
    path('transactions/batch/', TransactionBatchCreateView.as_view(), name='transactions-batch'),

    # Dataset templates
    path(
        'datasets/templates/<str:template_type>/<str:file_format>/',
        DatasetTemplateDownloadView.as_view(),
        name='dataset-template',
    ),
    path(
        'datasets/quality/<str:dataset_type>/',
        DatasetQualityView.as_view(),
        name='dataset-quality',
    ),

    # AI Features
    path('credit-score/analyze/', CreditScoreAnalyzeView.as_view(), name='credit-score'),
    path('credit-score/analyze/batch/', CreditScoreBatchAnalyzeView.as_view(), name='credit-score-batch'),
    path('fraud/analyze/', FraudAnalyzeView.as_view(), name='fraud-analyze'),
    path('fraud/analyze/batch/', FraudBatchAnalyzeView.as_view(), name='fraud-analyze-batch'),
    path('fraud/alerts/', FraudAlertListView.as_view(), name='fraud-alerts'),
    path('ai/insights/', AIInsightsView.as_view(), name='ai-insights'),

    # Analytics
    path('analytics/dashboard/', DashboardView.as_view(), name='dashboard'),

    # Users
    path('users/<uuid:user_id>/risk-profile/', UserRiskProfileView.as_view(), name='risk-profile'),
]
