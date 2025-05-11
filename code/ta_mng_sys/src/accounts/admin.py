from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, TAProfile, InstructorProfile, StaffProfile, Student

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, TAProfile, InstructorProfile, StaffProfile, Student

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("TA-Mgmt Info", {
            "fields": (
                "role",
                "employee_id",
                "department",
                "phone_number",
            ),
            "classes": ("wide",),
        }),
    )
    list_display = ("username", "email", "full_name", "role", "department", "is_staff", "is_active", "is_ta_coordinator")
    list_filter = ("role", "is_staff", "is_active", "department", "instructor_profile__is_ta_coordinator")
    search_fields = ("username", "email", "first_name", "last_name", "employee_id")
    ordering = ("username", "role")
    actions = ["make_ta_coordinator", "remove_ta_coordinator"]

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or "-"
    full_name.short_description = "Name"
    full_name.admin_order_field = "last_name"
    
    def is_ta_coordinator(self, obj):
        if obj.is_instructor():
            try:
                return obj.instructor_profile.is_ta_coordinator
            except AttributeError:
                pass
        return False
    is_ta_coordinator.short_description = "TA Coordinator"
    is_ta_coordinator.boolean = True
    
    def make_ta_coordinator(self, request, queryset):
        instructor_count = 0
        for user in queryset:
            if user.is_instructor():
                try:
                    profile = user.instructor_profile
                    if not profile.is_ta_coordinator:
                        profile.is_ta_coordinator = True
                        profile.save()
                        instructor_count += 1
                except InstructorProfile.DoesNotExist:
                    pass
        
        self.message_user(request, f"Made {instructor_count} instructors TA coordinators.")
    make_ta_coordinator.short_description = "Make selected instructors TA coordinators"
    
    def remove_ta_coordinator(self, request, queryset):
        instructor_count = 0
        for user in queryset:
            if user.is_instructor():
                try:
                    profile = user.instructor_profile
                    if profile.is_ta_coordinator:
                        profile.is_ta_coordinator = False
                        profile.save()
                        instructor_count += 1
                except InstructorProfile.DoesNotExist:
                    pass
        
        self.message_user(request, f"Removed {instructor_count} instructors from TA coordinator role.")
    remove_ta_coordinator.short_description = "Remove TA coordinator role from selected instructors"



@admin.register(TAProfile)
class TAProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "ta_type", "workload_info", "is_active", "is_assignable", "proctor_type")
    list_filter = ("ta_type", "is_active", "is_assignable", "proctor_type", "user__department")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__employee_id")
    filter_horizontal = ("assigned_course_offerings", "enrolled_course_offerings")
    readonly_fields = ("user_details",)
    
    fieldsets = (
        ("User Information", {
            "fields": ("user", "user_details")
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

    def workload_info(self, obj):
        if obj.max_workload == -1:
            return format_html(
                "<span style='color: #555;'>{} hours (no limit)</span>", 
                obj.total_workload
            )
        percentage = (obj.total_workload / obj.max_workload) * 100 if obj.max_workload > 0 else 0
        
        if percentage >= 90:
            color = 'red'
        elif percentage >= 75:
            color = 'orange'
        else:
            color = 'green'
            
        return format_html(
            "<span style='color: {};'>{}/{} hours ({}%)</span>",
            color, obj.total_workload, obj.max_workload, round(percentage)
        )
    workload_info.short_description = "Workload"
    
    def user_details(self, obj):
        return format_html(
            "<strong>Name:</strong> {} {}<br>"
            "<strong>Email:</strong> {}<br>"
            "<strong>Department:</strong> {}<br>"
            "<strong>Employee ID:</strong> {}<br>",
            obj.user.first_name, obj.user.last_name,
            obj.user.email,
            obj.user.department or "-",
            obj.user.employee_id or "-"
        )
    user_details.short_description = "User Details"

@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_faculty", "is_ta_coordinator", "is_active", "department", "course_count")
    list_filter = ("is_faculty", "is_ta_coordinator", "is_active", "user__department")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__employee_id")
    filter_horizontal = ("assigned_course_offerings",)
    readonly_fields = ("user_details",)
    
    fieldsets = (
        ("User Information", {
            "fields": ("user", "user_details")
        }),
        ("Status", {
            "fields": ("is_faculty", "is_active", "is_ta_coordinator")
        }),
        ("Course Assignments", {
            "fields": ("assigned_course_offerings",)
        }),
    )
    
    def department(self, obj):
        return obj.user.department or "-"
    department.admin_order_field = "user__department"
    
    def course_count(self, obj):
        count = obj.assigned_course_offerings.count()
        return format_html("<span>{}</span>", count)
    course_count.short_description = "Courses"
    
    def user_details(self, obj):
        return format_html(
            "<strong>Name:</strong> {} {}<br>"
            "<strong>Email:</strong> {}<br>"
            "<strong>Department:</strong> {}<br>"
            "<strong>Employee ID:</strong> {}<br>",
            obj.user.first_name, obj.user.last_name,
            obj.user.email,
            obj.user.department or "-",
            obj.user.employee_id or "-"
        )
    user_details.short_description = "User Details"

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "get_role", "get_department", "is_active")
    list_filter = ("is_active", "user__role", "user__department")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__employee_id")
    readonly_fields = ("user_details",)
    
    fieldsets = (
        ("User Information", {
            "fields": ("user", "user_details")
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
    )
    
    def get_role(self, obj):
        return obj.user.get_role_display()
    get_role.short_description = "Role"
    get_role.admin_order_field = "user__role"
    
    def get_department(self, obj):
        return obj.user.department or "-"
    get_department.short_description = "Department"
    get_department.admin_order_field = "user__department"
    
    def user_details(self, obj):
        return format_html(
            "<strong>Name:</strong> {} {}<br>"
            "<strong>Email:</strong> {}<br>"
            "<strong>Department:</strong> {}<br>"
            "<strong>Employee ID:</strong> {}<br>"
            "<strong>Phone:</strong> {}<br>",
            obj.user.first_name, obj.user.last_name,
            obj.user.email,
            obj.user.department or "-",
            obj.user.employee_id or "-",
            obj.user.phone_number or "-"
        )
    user_details.short_description = "User Details"

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "course_count")
    search_fields = ("student_id", "first_name", "last_name")
    filter_horizontal = ("enrolled_courses",)
    list_filter = ("enrolled_courses",)
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = "Name"
    
    def course_count(self, obj):
        count = obj.enrolled_courses.count()
        return count
    course_count.short_description = "Enrolled Courses"

# Register admin site customizations
admin.site.site_header = "TA Management System"
admin.site.site_title = "TA Management Admin"
admin.site.index_title = "Administration Portal"