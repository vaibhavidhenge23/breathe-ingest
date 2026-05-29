from django.db import models
from django.contrib.auth.models import User


class AuditLog(models.Model):
    """
    Har action ka record — approve, flag, edit.
    Production mein auditors yahi dekhte hain.
    """
    ACTION_APPROVE = 'approve'
    ACTION_FLAG = 'flag'
    ACTION_EDIT = 'edit'
    ACTION_UPLOAD = 'upload'
    ACTION_CHOICES = [
        (ACTION_APPROVE, 'Approved'),
        (ACTION_FLAG, 'Flagged'),
        (ACTION_EDIT, 'Edited'),
        (ACTION_UPLOAD, 'Uploaded'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    record_id = models.IntegerField(null=True, blank=True)
    batch_id = models.IntegerField(null=True, blank=True)
    detail = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} | {self.action} | {self.timestamp}"
