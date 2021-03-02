from django.contrib.gis.db import models as GISmodels
from django.db import models
from django.db.models.options import Options
from mptt.models import MPTTModel

from django_dal.managers import DALManager
from django_dal.mptt_managers import DALTreeManager
from django_dal.utils import check_permission

# Add `relations_limit` attribute to Meta class
if hasattr(models, 'options') and \
    hasattr(models.options, 'DEFAULT_NAMES') and \
    'relations_limit' not in models.options.DEFAULT_NAMES:
    models.options.DEFAULT_NAMES += ('relations_limit',)


class DALModel(GISmodels.Model):
    objects = DALManager()

    class Meta:
        relations_limit = []
        abstract = True

    def save(self,
             force_insert=False,
             force_update=False,
             using=None,
             update_fields=None,
             *args,
             **kwargs):

        if self.pk is None:
            check_permission(self, 'add')
        else:
            check_permission(self, 'change')

        super().save(force_insert=force_insert,
                     force_update=force_update,
                     using=using,
                     update_fields=update_fields)

    def delete(self,
               using=None,
               keep_parents=False,
               *args,
               **kwargs):

        check_permission(self, 'delete')

        super().delete(using=using,
                       keep_parents=keep_parents)


class DALMPTTModel(MPTTModel):
    objects = DALTreeManager()

    class Meta:
        relations_limit = []
        abstract = True

    def save(self,
             force_insert=False,
             force_update=False,
             using=None,
             update_fields=None,
             *args,
             **kwargs):

        if self.pk is None:
            check_permission(self, 'add')
        else:
            check_permission(self, 'change')

        super().save(force_insert=force_insert,
                     force_update=force_update,
                     using=using,
                     update_fields=update_fields)

    def delete(self,
               using=None,
               keep_parents=False,
               *args,
               **kwargs):

        check_permission(self, 'delete')

        super().delete(using=using,
                       keep_parents=keep_parents)
