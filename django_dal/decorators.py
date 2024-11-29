from functools import wraps

from django.http import HttpResponse

from django_dal.utils_authentication import authorize


def basic_login(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        logged, error = authorize(request)

        if error is not None:
            return HttpResponse("", status=403)
        return func(request, *args, **kwargs)

    return wrapper
