from functools import wraps

from django.contrib.auth.decorators import login_required as login_required_decorator


# Only Dash apps embedded in intranet-only pages should require authentication.
# Public dashboard apps must stay accessible without login.
PROTECTED_DASH_APPS = {
    "samplePerLabGraphic",
    "sampleVariantGraphic",
    "samplesReceivedOverTimeMap",
}


def selective_login_required(view_function, **kwargs):
    @wraps(view_function)
    def wrapped_view(request, *args, **view_kwargs):
        ident = view_kwargs.get("ident")
        if ident in PROTECTED_DASH_APPS:
            protected_view = login_required_decorator(view_function)
            return protected_view(request, *args, **view_kwargs)
        return view_function(request, *args, **view_kwargs)

    if getattr(view_function, "csrf_exempt", False):
        wrapped_view.csrf_exempt = True

    return wrapped_view
