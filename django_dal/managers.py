from inspect import signature

from django.db import models
from django.db.models import Q
from django.db.models.fields.related import ForeignObjectRel
from django.db.models.manager import Manager

from django_dal.query import DALQuerySet
from django_dal.utils import check_permission


class DALManager(Manager.from_queryset(DALQuerySet)):
    def _add_prefix(self, qset, prefix):
        # Recursive add prefix
        if isinstance(qset, Q) and hasattr(qset, 'children'):
            self._add_prefix(qset.children, prefix)
        # Add prefix
        elif isinstance(qset, list):
            for idx, q in enumerate(qset):
                if isinstance(q, tuple):
                    qset[idx] = ("{}__{}".format(prefix, q[0]), q[1])
                elif isinstance(q, Q) and hasattr(q, 'children'):
                    self._add_prefix(q.children, prefix)

    def _get_model(self, model, fields):
        split_fields = fields.split("__")
        field = model._meta.get_field(split_fields[0])
        if issubclass(type(field), models.ForeignKey):
            model = field.remote_field.get_related_field().model
        elif issubclass(type(field), ForeignObjectRel):
            model = field.related_model
        elif issubclass(type(field), models.ManyToManyField):
            model = field.remote_field.get_related_field().model
        if len(split_fields) > 1:
            return self._get_model(model, "__".join(split_fields[1:]))
        return model

    def get_queryset(self, ignore_filters=False):

        # raise exception if no permission
        check_permission(self.model, 'view')

        queryset = super().get_queryset()
        if ignore_filters is False:
            queryset = queryset.filter(self.get_filter())
        return queryset

    def all(self, ignore_filters=False):
        sig = signature(self.get_queryset)
        if sig.parameters.get('ignore_filters', None) is not None:
            return self.get_queryset(ignore_filters=ignore_filters)
        else:
            return self.get_queryset()

    def get_filter(self):
        qsets = Q()

        if hasattr(self.model._meta, 'relations_limit') and isinstance(self.model._meta.relations_limit, list):
            for relation_limit in self.model._meta.relations_limit:
                model = self._get_model(self.model, relation_limit)

                if model is not None and hasattr(model.objects, 'get_filter') and callable(model.objects.get_filter):
                    filters = model.objects.get_filter()
                    if isinstance(filters, Q):
                        self._add_prefix(qset=filters, prefix=relation_limit)
                        qsets &= filters

        return qsets
