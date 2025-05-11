import threading

# Thread-local storage to hold the current request
_local = threading.local()


class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store the request for later use
        if hasattr(request, 'user'):
            _local.user = request.user
        
        response = self.get_response(request)
        
        # Clean up after the request
        if hasattr(_local, 'user'):
            del _local.user
        
        return response


def get_current_user():
    """Get the user from the current request"""
    if hasattr(_local, 'user'):
        return _local.user
    return None