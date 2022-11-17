from django.urls import path

from django_dal.views import cxpr_info
from django_dal.views_mal import BaseSendFileView

urlpatterns = [
    path('cxpr/', cxpr_info),
    path('media/<path:path>', BaseSendFileView.as_view(), name='media_django_mal'),

]
