from rest_framework.authentication import BasicAuthentication

from django_dal.params import get_context_params


# verticalizzazione per impostare cxpr.user nelle richieste autenticate da rest_framework
class DALBasicAuthentication(BasicAuthentication):
    def authenticate(self, request):
        auth = super().authenticate(request)
        if auth is not None:
            request.user = auth[0]

            context_params = get_context_params()
            context_params.set_to_none()
            context_params.set_from_request(request)

        return auth
