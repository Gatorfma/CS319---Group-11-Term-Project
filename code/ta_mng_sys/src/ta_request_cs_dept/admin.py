from django.contrib import admin
from .models import (
    TARequest, 
    Semester,
    TAPreference, 
    GraderPreference, 
    MustHaveTAPreference,
    AvoidTAPreference, 
    AvoidGraderPreference
)

class TAPreferenceInline(admin.TabularInline):
    model = TAPreference
    extra = 1
    verbose_name = "Preferred TA"
    verbose_name_plural = "Preferred TAs"

class GraderPreferenceInline(admin.TabularInline):
    model = GraderPreference
    extra = 1
    verbose_name = "Preferred Grader"
    verbose_name_plural = "Preferred Graders"

class MustHaveTAPreferenceInline(admin.TabularInline):
    model = MustHaveTAPreference
    extra = 1
    verbose_name = "Must-have TA"
    verbose_name_plural = "Must-have TAs"

class AvoidTAPreferenceInline(admin.TabularInline):
    model = AvoidTAPreference
    extra = 1
    verbose_name = "TA to Avoid"
    verbose_name_plural = "TAs to Avoid"

class AvoidGraderPreferenceInline(admin.TabularInline):
    model = AvoidGraderPreference
    extra = 1
    verbose_name = "Grader to Avoid"
    verbose_name_plural = "Graders to Avoid"

@admin.register(TARequest)
class TARequestAdmin(admin.ModelAdmin):
    # Removed 'status' from list_display and list_filter
    list_display = ('course', 'semester', 'instructor', 'min_ta_loads', 'max_ta_loads', 'graders_requested', 'created_at')
    list_filter = ('semester', 'course', 'instructor')
    search_fields = ('course__code', 'course__title', 'instructor__username', 'instructor__first_name', 'instructor__last_name')
    date_hierarchy = 'created_at'
    
    inlines = [
        TAPreferenceInline,
        GraderPreferenceInline,
        MustHaveTAPreferenceInline,
        AvoidTAPreferenceInline,
        AvoidGraderPreferenceInline,
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'semester', 'instructor')
        }),
        ('TA Requirements', {
            'fields': ('min_ta_loads', 'max_ta_loads', 'graders_requested')
        }),
        # Removed 'Status' section since there's no status field
        ('Justification', {
            'fields': ('must_have_justification', 'general_justification'),
            'classes': ('collapse',),
        }),
    )

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    # Replaced is_request_period_open with a custom method
    list_display = ('name', 'start_date', 'end_date', 'is_active', 'is_request_period_active')
    list_filter = ('is_active',)  # Removed is_request_period_open
    search_fields = ('name',)
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Semester Information', {
            'fields': ('name', 'start_date', 'end_date', 'request_start_date', 'request_end_date')
        }),
        ('Status', {
            'fields': ('is_active', 'ta_coordinator')
        }),
    )
    
    # Add a method to make is_request_period_active usable in list_display
    def is_request_period_active(self, obj):
        return obj.is_request_period_active()
    is_request_period_active.short_description = "Request Period Active"
    is_request_period_active.boolean = True  # Display as icon

@admin.register(TAPreference)
class TAPreferenceAdmin(admin.ModelAdmin):
    list_display = ('ta', 'ta_request', 'preference_order')
    list_filter = ('ta_request__course', 'ta_request__semester')
    search_fields = ('ta__user__username', 'ta__user__first_name', 'ta_request__course__code')

@admin.register(GraderPreference)
class GraderPreferenceAdmin(admin.ModelAdmin):
    list_display = ('ta', 'ta_request', 'preference_order')
    list_filter = ('ta_request__course', 'ta_request__semester')
    search_fields = ('ta__user__username', 'ta__user__first_name', 'ta_request__course__code')

@admin.register(MustHaveTAPreference)
class MustHaveTAPreferenceAdmin(admin.ModelAdmin):
    list_display = ('ta', 'ta_request', 'preference_order')
    list_filter = ('ta_request__course', 'ta_request__semester')
    search_fields = ('ta__user__username', 'ta__user__first_name', 'ta_request__course__code')

@admin.register(AvoidTAPreference)
class AvoidTAPreferenceAdmin(admin.ModelAdmin):
    list_display = ('ta', 'ta_request', 'preference_order')
    list_filter = ('ta_request__course', 'ta_request__semester')
    search_fields = ('ta__user__username', 'ta__user__first_name', 'ta_request__course__code')

@admin.register(AvoidGraderPreference)
class AvoidGraderPreferenceAdmin(admin.ModelAdmin):
    list_display = ('ta', 'ta_request', 'preference_order')
    list_filter = ('ta_request__course', 'ta_request__semester')
    search_fields = ('ta__user__username', 'ta__user__first_name', 'ta_request__course__code')