from django.db import models
from django.conf import settings

class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='User who will receive this notification'
    )
    message = models.TextField(
        help_text='Content of the notification'
    )
    notification_type = models.CharField(
        max_length=50,
        blank=True,
        help_text='Category or type of notification (e.g., "SwapRequest", "LeaveApproval")'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When the notification was created'
    )
    is_read = models.BooleanField(
        default=False,
        help_text='Marks whether the recipient has read the notification'
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"Notification to {self.recipient.username} at {self.timestamp}"
