from django.contrib import admin
from .models import (
    LabDuty,
    GradingDuty,
    RecitationDuty,
    OfficeHourDuty,
    ProctoringDuty,
    TACourseAssignment,
    DutyLog
)
from django.utils import timezone

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

@admin.register(TACourseAssignment)
class TACourseAssignmentAdmin(admin.ModelAdmin):
    list_display   = ('ta', 'offering')
    list_filter    = ('offering__course', 'offering__semester')
    search_fields  = ('ta__user__username', 'offering__course__code')

@admin.register(DutyLog)
class DutyLogAdmin(admin.ModelAdmin):
    list_display    = (
        'ta_profile',
        'get_duty',
        'hours_spent',
        'status',
        'date_logged',
        'processed_by',
        'processed_at',
    )
    list_filter     = ('status', 'duty_content_type')
    search_fields   = ('ta_profile__user__username', 'duty_object_id')
    raw_id_fields   = (
        'duty_content_type',
        'ta_profile',
        'processed_by',
    )
    readonly_fields = ('date_logged', 'processed_at')
    actions         = ('approve_logs', 'reject_logs',)

    def get_duty(self, obj):
        return obj.duty
    get_duty.short_description = 'Duty'

    def approve_logs(self, request, queryset):
        updated = queryset.update(
            status='A',
            processed_by=request.user,
            processed_at=timezone.now()
        )
        self.message_user(request, f"{updated} log approved.")
    approve_logs.short_description = "Approve selected logs"

    def reject_logs(self, request, queryset):
        updated = queryset.update(
            status='R',
            processed_by=request.user,
            processed_at=timezone.now()
        )
        self.message_user(request, f"{updated} log rejected.")
    reject_logs.short_description = "Reject selected logs"

