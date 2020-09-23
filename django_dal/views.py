from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django_dal.params import copa
from users.models import User, Group


# debug
def get_copa_user_name():
    return copa.user.username


@login_required
@user_passes_test(lambda u: u.is_superuser)
def copa_info(request):
    response = 'Context parameters:\n{}'.format(copa.describe())

    # debug
    # response += '\n\nuser = {}'.format(copa.user)
    # user = User.objects.get(username='apptest')
    # user_name = copa.run({'user': user}, get_copa_user_name)
    # response += '\n\nuser = {}'.format(user_name)
    # response += '\n\nuser = {}'.format(copa.user)

    return HttpResponse(response, content_type='text/plain')
