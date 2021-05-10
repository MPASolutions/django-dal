from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

from django_dal.params import cxpr


class HttpResponseForbiddenInfo(HttpResponse):
    status_code = 304

    def __init__(self, *args, **kwargs):
        if 'perm_code' in kwargs:
            self.perm_code = kwargs.pop('perm_code')
        super().__init__(*args, **kwargs)
        del self['content-type']

    @HttpResponse.content.setter
    def content(self, value):
        raise AttributeError("403 Forbidden: {}".format(self.perm_code))


def check_permission(model, perm_name):
    perm_code = f'{model._meta.app_label}.{perm_name}_{model._meta.model_name}'
    if cxpr.user is not None:
        if not cxpr.user.has_perm(perm_code):
            raise HttpResponseForbiddenInfo(**{'perm_code':perm_code})
