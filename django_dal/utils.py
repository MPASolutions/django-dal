
from django_dal.params import cxpr
from django.core.exceptions import PermissionDenied

def check_permission(model, perm_name):
    perm_code = f'{model._meta.app_label}.{perm_name}_{model._meta.model_name}'
    if cxpr.user is not None:
        if not cxpr.user.has_perm(perm_code):
            raise PermissionDenied(perm_code)

#    if cxpr.group is not None:
#        if not cxpr.group.has_perm(perm_code):
#            raise PermissionDenied(perm_code)
