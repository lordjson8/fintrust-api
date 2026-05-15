from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.credit_scoring.models import RiskProfile
from apps.fraud_detection.models import FraudAlert
from apps.transactions.models import Transaction
from apps.users.models import User


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            full_name='Admin User',
            password='password123',
        )
        self.analyst = User.objects.create_user(
            email='analyst@example.com',
            full_name='Analyst One',
            password='password123',
        )
        self.other_analyst = User.objects.create_user(
            email='other@example.com',
            full_name='Analyst Two',
            password='password123',
        )
        self.analyst_txn = Transaction.objects.create(
            user=self.analyst,
            amount=Decimal('1000.00'),
            type='credit',
        )
        self.other_txn = Transaction.objects.create(
            user=self.other_analyst,
            amount=Decimal('2000.00'),
            type='debit',
        )
        RiskProfile.objects.create(
            user=self.analyst,
            risk_score=82,
            repayment_probability=0.86,
            recommended_loan=Decimal('250000.00'),
        )
        RiskProfile.objects.create(
            user=self.other_analyst,
            risk_score=31,
            repayment_probability=0.28,
            recommended_loan=Decimal('0.00'),
        )
        FraudAlert.objects.create(
            transaction=self.analyst_txn,
            fraud_probability=10,
            urgency='LOW',
            action='ALLOW',
        )
        FraudAlert.objects.create(
            transaction=self.other_txn,
            fraud_probability=90,
            urgency='HIGH',
            action='BLOCK',
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_analyst_only_lists_own_transactions(self):
        self.authenticate(self.analyst)

        response = self.client.get('/api/v1/transactions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transaction_ids = {item['id'] for item in response.json()}
        self.assertEqual(transaction_ids, {str(self.analyst_txn.id)})

    def test_admin_lists_all_transactions(self):
        self.authenticate(self.admin)

        response = self.client.get('/api/v1/transactions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transaction_ids = {item['id'] for item in response.json()}
        self.assertEqual(transaction_ids, {str(self.analyst_txn.id), str(self.other_txn.id)})

    def test_analyst_cannot_create_transaction_for_another_user(self):
        self.authenticate(self.analyst)

        response = self.client.post(
            '/api/v1/transactions/',
            {
                'user': str(self.other_analyst.id),
                'amount': '3000.00',
                'type': 'transfer',
                'payment_method': 'mobile_money',
                'location': 'Douala',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Transaction.objects.get(id=response.json()['id'])
        self.assertEqual(created.user, self.analyst)

    def test_analyst_cannot_read_other_user_risk_profile(self):
        self.authenticate(self.analyst)

        response = self.client.get(f'/api/v1/users/{self.other_analyst.id}/risk-profile/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_analyst_dashboard_is_scoped_to_own_data(self):
        self.authenticate(self.analyst)

        response = self.client.get('/api/v1/analytics/dashboard/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['kpis']['total_transactions'], 1)
        self.assertEqual(data['kpis']['total_customers'], 1)
        self.assertEqual(data['kpis']['active_fraud_alerts'], 0)
        self.assertEqual(len(data['recent_transactions']), 1)
        self.assertEqual(len(data['recent_alerts']), 1)
        self.assertEqual(data['recent_transactions'][0]['user__full_name'], self.analyst.full_name)

    def test_analyst_only_lists_own_fraud_alerts(self):
        self.authenticate(self.analyst)

        response = self.client.get('/api/v1/fraud/alerts/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alert_ids = {item['transaction'] for item in response.json()}
        self.assertEqual(alert_ids, {str(self.analyst_txn.id)})

    def test_analyst_cannot_score_another_user(self):
        self.authenticate(self.analyst)

        response = self.client.post(
            '/api/v1/credit-score/analyze/',
            {
                'user_id': str(self.other_analyst.id),
                'monthly_income': 100000,
                'mobile_money_frequency': 12,
                'late_payments': 1,
                'account_age_months': 9,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
