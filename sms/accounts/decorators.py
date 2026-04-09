from django.shortcuts import redirect
from accounts.models import Profile

def role_required(role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # If user has no profile, deny access safely
            if not hasattr(request.user, 'profile'):
                return redirect('login')

            if request.user.profile.role != role:
                return redirect('login')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
