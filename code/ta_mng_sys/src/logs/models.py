from django.db import models
from django.conf import settings


class Log(models.Model):
    """
    Model to store logs of user actions in the system.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='action_logs',
        help_text='User who performed the action'
    )
    action = models.CharField(max_length=255, help_text='Description of the action')
    model_name = models.CharField(max_length=100, help_text='Name of the model affected')
    object_id = models.CharField(max_length=50, blank=True, null=True, help_text='ID of the object affected')
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Action Log'
        verbose_name_plural = 'Action Logs'
    
    def __str__(self):
        return f"{self.timestamp}: {self.user} - {self.action}"