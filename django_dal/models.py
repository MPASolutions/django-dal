from django.apps import apps
from django.db import models
from mptt.models import MPTTModel

from django_dal.managers import DALManager
from django_dal.mptt_managers import DALTreeManager
from django_dal.utils import check_permission

if apps.is_installed("django.contrib.gis"):
    from django.contrib.gis.db.models import Model
else:
    from django.db.models import Model

# Add `relations_limit` attribute to Meta class

test_1 = hasattr(models, "options")
test_2 = hasattr(models.options, "DEFAULT_NAMES")
test_3 = "relations_limit" not in models.options.DEFAULT_NAMES

if test_1 and test_2 and test_3:
    models.options.DEFAULT_NAMES += ("relations_limit",)


class DALModel(Model):
    objects = DALManager()

    class Meta:
        relations_limit = []
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, *args, **kwargs):

        if self.pk is None:
            check_permission(self, "add")
        else:
            check_permission(self, "change")

        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
            *args,
            **kwargs
        )

    def delete(self, using=None, keep_parents=False, *args, **kwargs):

        check_permission(self, "delete")

        super().delete(using=using, keep_parents=keep_parents)


class DALMPTTModel(MPTTModel):
    objects = DALTreeManager()

    class Meta:
        relations_limit = []
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, *args, **kwargs):

        if self.pk is None:
            check_permission(self, "add")
        else:
            check_permission(self, "change")

        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def delete(self, using=None, keep_parents=False, *args, **kwargs):

        check_permission(self, "delete")

        super().delete(using=using, keep_parents=keep_parents)
