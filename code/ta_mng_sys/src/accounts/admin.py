from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, TAProfile, InstructorProfile, StaffProfile

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("TA-Mgmt Info", {
            "fields": (
                "role",
                "employee_id",
                "department",
                "phone_number",
            )
        }),
    )
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active", "department")
    search_fields = ("username", "email", "first_name", "last_name", "employee_id")

@admin.register(TAProfile)
class TAProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "ta_type", "is_active", "is_assignable", "proctor_type", 
                   "total_workload", "max_workload")
    list_filter = ("ta_type", "is_active", "is_assignable", "proctor_type")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    filter_horizontal = ("assigned_course_offerings", "enrolled_course_offerings")
    fieldsets = (
        ("User Information", {
            "fields": ("user",)
        }),
        ("Status", {
            "fields": ("ta_type", "is_active", "is_assignable", "proctor_type")
        }),
        ("Workload Settings", {
            "fields": ("total_workload", "max_workload", "max_absent_days")
        }),
        ("Course Assignments", {
            "fields": ("assigned_course_offerings", "enrolled_course_offerings")
        }),
    )

@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_faculty", "is_active")
    list_filter = ("is_faculty", "is_active")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    filter_horizontal = ("assigned_course_offerings",)
    fieldsets = (
        ("User Information", {
            "fields": ("user",)
        }),
        ("Status", {
            "fields": ("is_faculty", "is_active")
        }),
        ("Course Assignments", {
            "fields": ("assigned_course_offerings",)
        }),
    )



# Add after other admin registrations
@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "get_role", "is_active")
    list_filter = ("is_active", "user__role")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    
    def get_role(self, obj):
        return obj.user.get_role_display()
    get_role.short_description = "Role"
    get_role.admin_order_field = "user__role"