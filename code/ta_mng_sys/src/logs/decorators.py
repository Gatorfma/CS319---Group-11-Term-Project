import functools
from .utils import log_action


def log_view_action(action_description):
    """
    Decorator to log view actions.
    
    Example:
        @log_view_action("viewed user details")
        def user_detail_view(request, pk):
            ...
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Execute the view function
            response = view_func(request, *args, **kwargs)
            
            # Log the action if user is authenticated
            if request.user.is_authenticated:
                log_action(
                    user=request.user,
                    action=action_description,
                    model_name=view_func.__name__,
                    object_id=kwargs.get('pk') or kwargs.get('id')
                )
            
            return response
        return wrapped_view
    return decorator