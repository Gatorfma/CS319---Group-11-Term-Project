from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

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
