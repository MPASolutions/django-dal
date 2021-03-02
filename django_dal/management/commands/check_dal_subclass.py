# -*- coding: utf-8 -*-

from django.apps import apps
from django.core.management.base import BaseCommand

from django_dal.managers import DALManager
from django_dal.models import DALModel, DALMPTTModel
from django_dal.mptt_managers import DALTreeManager


class Command(BaseCommand):
    '''
    python manage.py check_dal_subclass
    '''
    help = "Command for check if all models and managers are sublcass of DAL package"

    def handle(self, *args, **options):

        for model in apps.get_models():
            test_model = issubclass(model, DALModel) or \
                         issubclass(model, DALMPTTModel)
            test_manager = issubclass(model.objects.__class__, DALManager) or \
                           issubclass(model.objects.__class__, DALTreeManager)
            if test_model == False or test_manager == False:
                print("{}.{} TEST model: {} TEST manager: {}".format(model._meta.app_label, model._meta.model_name,
                                                                     test_model, test_manager))
