from django.urls import path

from django_dal.views import *

urlpatterns = [
    path('cxpr/', cxpr_info),
]
