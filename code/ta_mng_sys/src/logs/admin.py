from django.contrib import admin
from .models import Log


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_id')
    list_filter = ('timestamp', 'model_name', 'user')
    search_fields = ('action', 'user__username', 'model_name', 'object_id')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp', 'user', 'action', 'model_name', 'object_id')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser