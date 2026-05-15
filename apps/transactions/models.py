import uuid
from django.db import models
from apps.users.models import User


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('transfer', 'Transfer'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('bank', 'Bank'),
        ('cash', 'Cash'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='mobile_money')
    location = models.CharField(max_length=100, default='Yaoundé')
    timestamp = models.DateTimeField(auto_now_add=True)
    device_change = models.BooleanField(default=False)

    class Meta:
        db_table = 'transactions'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user.full_name} — {self.type} {self.amount} XAF'
