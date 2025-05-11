from django.contrib import admin
from .models import (
    SwapRequest,
    LeaveRequest
)

# Register your models here.
@admin.register(SwapRequest)
class SwapRequestAdmin(admin.ModelAdmin):
    list_display = (
        'duty_content_type', 'duty_object_id', 'from_ta', 'to_ta', 'status', 'requested_at', 'responded_at', 'processed_by'
    )
    list_filter = ('status', 'requested_at')
    search_fields = (
        'from_ta__user__username',
        'to_ta__user__username',
        'duty_object_id'
    )

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        'ta_profile',
        'start_date',
        'end_date',
        'status',
        'submitted_at',
        'processed_by',
        'processed_at'
    )
    list_filter = ('status', 'submitted_at')
    search_fields = (
        'ta_profile__user__username',
        'ta_profile__user__first_name',
        'ta_profile__user__last_name',
    )
    readonly_fields = ('submitted_at',)