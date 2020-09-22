from django.db import models
from django.db.models.options import Options

from django_dal.managers import DALManager

# Add `relations_limit` attribute to Meta class
if hasattr(models, 'options') and \
    hasattr(models.options, 'DEFAULT_NAMES') and \
    'relations_limit' not in models.options.DEFAULT_NAMES:
    models.options.DEFAULT_NAMES += ('relations_limit',)


class DALModel(models.Model):
    objects = LimitManager()

    class Meta:
        relations_limit = []
        abstract = True

