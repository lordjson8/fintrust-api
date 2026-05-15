"""
Management command to seed demo data.
Usage: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
import uuid

from apps.users.models import User
from apps.transactions.models import Transaction
from apps.credit_scoring.models import RiskProfile
from apps.fraud_detection.models import FraudAlert


DEMO_USERS = [
    {
        'full_name': 'Jean Pierre Mvondo',
        'email': 'jp.mvondo@demo.com',
        'password': 'demo1234',
        'role': 'analyst',
        'monthly_income': 180000,
        'mm_frequency': 52,
        'late_payments': 1,
        'risk_score': 81,
        'repayment_prob': 0.87,
        'recommended_loan': 250000,
        'summary': 'Stable income with consistent mobile money activity. Low late payment history indicates reliable repayment behavior.',
    },
    {
        'full_name': 'Aminata Diallo',
        'email': 'aminata.diallo@demo.com',
        'password': 'demo1234',
        'role': 'analyst',
        'monthly_income': 95000,
        'mm_frequency': 28,
        'late_payments': 4,
        'risk_score': 44,
        'repayment_prob': 0.52,
        'recommended_loan': 80000,
        'summary': 'Moderate transaction frequency with elevated late payment history. Credit limit recommended at 80% of standard.',
    },
    {
        'full_name': 'Emmanuel Talla',
        'email': 'emmanuel.talla@demo.com',
        'password': 'demo1234',
        'role': 'analyst',
        'monthly_income': 320000,
        'mm_frequency': 88,
        'late_payments': 0,
        'risk_score': 94,
        'repayment_prob': 0.96,
        'recommended_loan': 500000,
        'summary': 'Exceptional financial profile with high mobile money volume and zero late payments. Premium credit candidate.',
    },
    {
        'full_name': 'Fatou Ndiaye',
        'email': 'fatou.ndiaye@demo.com',
        'password': 'demo1234',
        'role': 'analyst',
        'monthly_income': 60000,
        'mm_frequency': 12,
        'late_payments': 8,
        'risk_score': 22,
        'repayment_prob': 0.28,
        'recommended_loan': 0,
        'summary': 'High risk profile due to frequent late payments and low transaction frequency. Loan application rejected pending improvement.',
    },
]

LOCATIONS = ['Yaoundé', 'Douala', 'Bafoussam', 'Garoua', 'Bamenda', 'Maroua']
PAYMENT_METHODS = ['mobile_money', 'mobile_money', 'mobile_money', 'bank', 'cash']
TXN_TYPES = ['credit', 'debit', 'debit', 'transfer']


class Command(BaseCommand):
    help = 'Seed demo data for FinTrust AI'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding demo data...')

        # Create admin
        if not User.objects.filter(email='admin@fintrust.ai').exists():
            User.objects.create_superuser(
                email='admin@fintrust.ai',
                full_name='Admin FinTrust',
                password='admin1234',
            )
            self.stdout.write('  ✅ Admin created: admin@fintrust.ai / admin1234')

        created_users = []
        for user_data in DEMO_USERS:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'full_name': user_data['full_name'],
                    'role': user_data['role'],
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()

            # Create risk profile
            RiskProfile.objects.get_or_create(
                user=user,
                defaults={
                    'risk_score': user_data['risk_score'],
                    'repayment_probability': user_data['repayment_prob'],
                    'recommended_loan': user_data['recommended_loan'],
                    'ai_summary': user_data['summary'],
                }
            )

            created_users.append((user, user_data))
            self.stdout.write(f'  ✅ User: {user.full_name}')

        # Create transactions (5 per user = 20 total)
        Transaction.objects.all().delete()
        all_transactions = []
        for user, user_data in created_users:
            for i in range(5):
                days_ago = random.randint(1, 60)
                txn = Transaction.objects.create(
                    user=user,
                    amount=random.randint(5000, user_data['monthly_income'] // 2),
                    type=random.choice(TXN_TYPES),
                    payment_method=random.choice(PAYMENT_METHODS),
                    location=random.choice(LOCATIONS),
                    device_change=random.random() < 0.15,
                    timestamp=timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23)),
                )
                all_transactions.append(txn)

        self.stdout.write(f'  ✅ {len(all_transactions)} transactions created')

        # Create the demo fraud transaction (Aminata, high fraud)
        aminata = User.objects.get(email='aminata.diallo@demo.com')
        fraud_txn = Transaction.objects.create(
            id=uuid.UUID('00000000-0000-0000-0000-000000000082'),
            user=aminata,
            amount=750000,
            type='transfer',
            payment_method='mobile_money',
            location='Yaoundé',
            device_change=True,
            timestamp=timezone.now() - timedelta(hours=2),
        )
        FraudAlert.objects.get_or_create(
            transaction=fraud_txn,
            defaults={
                'fraud_probability': 91,
                'urgency': 'HIGH',
                'explanation': 'Transaction amount exceeds 5x user average with simultaneous device change detected. Geographic pattern inconsistency identified.',
                'indicators': [
                    'Amount 8x above user average',
                    'Device fingerprint changed within 30 min',
                    'Unusual transfer destination',
                ],
                'action': 'BLOCK',
            }
        )
        self.stdout.write('  ✅ Demo fraud alert seeded (TXN-2026-0082)')

        # Create a few more alerts for dashboard variety
        low_risk_txn = Transaction.objects.create(
            user=User.objects.get(email='emmanuel.talla@demo.com'),
            amount=45000,
            type='debit',
            payment_method='mobile_money',
            location='Douala',
            device_change=False,
        )
        FraudAlert.objects.get_or_create(
            transaction=low_risk_txn,
            defaults={
                'fraud_probability': 12,
                'urgency': 'LOW',
                'explanation': 'Normal transaction pattern within expected parameters.',
                'indicators': ['Within normal range'],
                'action': 'ALLOW',
            }
        )

        medium_txn = Transaction.objects.create(
            user=User.objects.get(email='fatou.ndiaye@demo.com'),
            amount=280000,
            type='transfer',
            payment_method='mobile_money',
            location='Bafoussam',
            device_change=True,
        )
        FraudAlert.objects.get_or_create(
            transaction=medium_txn,
            defaults={
                'fraud_probability': 58,
                'urgency': 'MEDIUM',
                'explanation': 'Transfer amount above average with device change. Monitor for follow-up activity.',
                'indicators': ['Device change detected', 'Amount above 30-day average'],
                'action': 'FLAG',
            }
        )

        self.stdout.write(self.style.SUCCESS('\n🎉 Demo data seeded successfully!'))
        self.stdout.write('\nDemo login credentials:')
        self.stdout.write('  Admin:    admin@fintrust.ai / admin1234')
        self.stdout.write('  Analyst:  jp.mvondo@demo.com / demo1234')
