from django.contrib import admin
from .models import (
    LabDuty,
    GradingDuty,
    RecitationDuty,
    OfficeHourDuty,
    ProctoringDuty,
    SwapRequest,
    LeaveRequest
)

class DutyAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'offering', 'date', 'start_time', 'end_time', 'assigned_ta', 'status'
    )
    list_filter = ('status', 'date', 'offering__semester')
    search_fields = (
        'offering__course__department_code',
        'offering__course__course_code',
        'offering__course__title',
    )


@admin.register(LabDuty)
class LabDutyAdmin(DutyAdmin):
    list_display = DutyAdmin.list_display + ('lab_number',)


@admin.register(GradingDuty)
class GradingDutyAdmin(DutyAdmin):
    list_display = DutyAdmin.list_display + ('grading_type',)


@admin.register(RecitationDuty)
class RecitationDutyAdmin(DutyAdmin):
    list_display = DutyAdmin.list_display + ('topic',)


@admin.register(OfficeHourDuty)
class OfficeHourDutyAdmin(DutyAdmin):
    list_display = DutyAdmin.list_display + ('location',)


@admin.register(ProctoringDuty)
class ProctoringDutyAdmin(DutyAdmin):
    list_display = DutyAdmin.list_display + ('exam',)
    
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
