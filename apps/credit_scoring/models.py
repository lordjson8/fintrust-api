import uuid
from django.db import models
from apps.users.models import User


class RiskProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='risk_profiles')
    risk_score = models.IntegerField(default=0)  # 0–100
    repayment_probability = models.FloatField(default=0.0)  # 0.0–1.0
    recommended_loan = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ai_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'risk_profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.full_name} — score {self.risk_score}'
