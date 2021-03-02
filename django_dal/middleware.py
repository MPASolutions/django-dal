from django_dal.params import get_context_params


class ContextParamsMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        context_params = get_context_params()
        context_params.set_from_request(request)

        response = self.get_response(request)
        return response
