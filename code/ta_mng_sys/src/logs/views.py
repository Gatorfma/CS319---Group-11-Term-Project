from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from .models import Log

def is_staff_or_admin(user):
    """Check if user is staff, superuser, or has any admin-level role except TA"""
    return (user.is_staff or 
            user.is_superuser or 
            (user.role in [user.Roles.SECRETARY, user.Roles.DEPT_CHAIR, user.Roles.ADMIN, user.Roles.INSTRUCTOR] and 
             user.role != user.Roles.TA))

@login_required
def logs_dashboard(request):
    """Dashboard view for viewing and filtering logs"""
    # Check if user has permission to view logs
    if not is_staff_or_admin(request.user):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # Get query parameters
    search_query = request.GET.get('search', '')
    model_filter = request.GET.get('model', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Start with all logs
    logs = Log.objects.all()
    
    # Apply filters
    if search_query:
        logs = logs.filter(action__icontains=search_query)
    
    if model_filter:
        logs = logs.filter(model_name=model_filter)
    
    if user_filter:
        logs = logs.filter(user__username=user_filter)
    
    if date_from:
        logs = logs.filter(timestamp__gte=date_from)
    
    if date_to:
        logs = logs.filter(timestamp__lte=date_to)
    
    # Paginate results
    paginator = Paginator(logs.order_by('-timestamp'), 50)  # 50 logs per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get unique values for filters
    model_names = Log.objects.values_list('model_name', flat=True).distinct()
    usernames = Log.objects.exclude(user=None).values_list('user__username', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'model_filter': model_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'model_names': model_names,
        'usernames': usernames,
    }
    
    return render(request, 'logs/dashboard.html', context)

@login_required
def object_logs(request, model_name, object_id):
    """View logs for a specific object"""
    # Check if user has permission to view logs
    if not is_staff_or_admin(request.user):
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    logs = Log.objects.filter(
        model_name=model_name,
        object_id=str(object_id)
    ).order_by('-timestamp')
    
    context = {
        'logs': logs,
        'model_name': model_name,
        'object_id': object_id,
    }
    
    return render(request, 'logs/object_logs.html', context)