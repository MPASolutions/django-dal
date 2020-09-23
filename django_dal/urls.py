from django.urls import path
from django_dal.views import *

urlpatterns = [
    path('copa/', copa_info),
]