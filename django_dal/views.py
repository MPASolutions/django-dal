from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse

from django_dal.params import cxpr


@login_required
@user_passes_test(lambda u: u.is_superuser)
def cxpr_info(request):
    response = "Context parameters:\n{}".format(cxpr.describe())
    response += "\n\nJSON:\n" + cxpr.get_values_json_str()
    response += "\n\nChecksum:\n" + cxpr.get_checksum()

    return HttpResponse(response, content_type="text/plain")
