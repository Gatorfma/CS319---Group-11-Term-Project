# notifications/admin.py

from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'timestamp', 'is_read')
    list_filter = ('is_read', 'notification_type')
    search_fields = ('recipient__username', 'message')
    ordering = ('-timestamp',)
    list_per_page = 25
