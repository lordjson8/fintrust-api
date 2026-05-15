import uuid
from django.db import models
from apps.transactions.models import Transaction


class FraudAlert(models.Model):
    URGENCY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    ACTION_CHOICES = [
        ('ALLOW', 'Allow'),
        ('FLAG', 'Flag'),
        ('BLOCK', 'Block'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.OneToOneField(
        Transaction, on_delete=models.CASCADE, related_name='fraud_alert'
    )
    fraud_probability = models.IntegerField(default=0)  # 0–100
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='LOW')
    explanation = models.TextField(blank=True)
    indicators = models.JSONField(default=list)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default='ALLOW')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fraud_alerts'
        ordering = ['-created_at']

    def __str__(self):
        return f'Alert {self.urgency} — {self.fraud_probability}% — {self.action}'
