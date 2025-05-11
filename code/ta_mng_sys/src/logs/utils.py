from .models import Log


def log_action(user, action, model_name=None, object_id=None):
    """
    Create a log entry for a user action.
    
    Args:
        user: The user who performed the action
        action: Description of the action
        model_name: Optional name of the model affected
        object_id: Optional ID of the object affected
    
    Returns:
        The created Log instance
    """
    return Log.objects.create(
        user=user,
        action=action,
        model_name=model_name or '',
        object_id=str(object_id) if object_id else None
    )