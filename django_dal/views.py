from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django_dal.params import cxpr
from users.models import User, Group


# debug
def get_cxpr_user_name():
    return cxpr.user.username


@login_required
@user_passes_test(lambda u: u.is_superuser)
def cxpr_info(request):
    response = 'Context parameters:\n{}'.format(cxpr.describe())

    # debug
    # response += '\n\nuser = {}'.format(cxpr.user)
    # user = User.objects.get(username='apptest')
    # user_name = cxpr.run({'user': user}, get_cxpr_user_name)
    # response += '\n\nuser = {}'.format(user_name)
    # response += '\n\nuser = {}'.format(v.user)

    return HttpResponse(response, content_type='text/plain')
