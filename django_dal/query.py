from itertools import chain

from django.db.models.query import QuerySet
from django.db.models.query_utils import FilteredRelation
from django.db.models.utils import resolve_callables
from mptt.querysets import TreeQuerySet

from django_dal.utils import check_permission


class DALQuerySet(QuerySet):

    def update(self, **kwargs):
        # raise exception if no permission
        check_permission(self.model, 'change')
        return super().update(**kwargs)

    def delete(self):
        # raise exception if no permission
        check_permission(self.model, 'delete')
        return super().delete()

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        # raise exception if no permission
        check_permission(self.model, 'add')
        return super().bulk_create(objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts)

    def bulk_update(self, objs, fields, batch_size=None):
        # raise exception if no permission
        check_permission(self.model, 'change')
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def update_or_create(self, defaults=None, **kwargs):
        defaults = defaults or {}
        self._for_write = True
        obj, created = self.get_or_create(defaults, **kwargs)
        if created:
            return obj, created
        for k, v in resolve_callables(defaults):
            setattr(obj, k, v)
        obj.save(using=self.db)
        return obj, False

    def _annotate(self, args, kwargs, select=True):
        self._validate_values_are_expressions(
            args + tuple(kwargs.values()), method_name="annotate"
        )
        annotations = {}
        for arg in args:
            # The default_alias property may raise a TypeError.
            try:
                if arg.default_alias in kwargs:
                    raise ValueError(
                        "The named annotation '%s' conflicts with the "
                        "default name for another annotation." % arg.default_alias
                    )
            except TypeError:
                raise TypeError("Complex annotations require an alias")
            annotations[arg.default_alias] = arg
        annotations.update(kwargs)

        clone = self._chain()
        names = self._fields
        if names is None:
            names = set(
                chain.from_iterable(
                    (field.name, field.attname)
                    if hasattr(field, "attname")
                    else (field.name,)
                    for field in self.model._meta.get_fields()
                )
            )

        for alias, annotation in annotations.items():
            #            if alias in names:
            #                raise ValueError(
            #                    "The annotation '%s' conflicts with a field on "
            #                    "the model." % alias
            #                )
            if isinstance(annotation, FilteredRelation):
                clone.query.add_filtered_relation(annotation, alias)
            else:
                clone.query.add_annotation(
                    annotation,
                    alias,
                    select=select,
                )
        for alias, annotation in clone.query.annotations.items():
            if alias in annotations and annotation.contains_aggregate:
                if clone._fields is None:
                    clone.query.group_by = True
                else:
                    clone.query.set_group_by()
                break

        return clone


class DALTreeQuerySet(TreeQuerySet, DALQuerySet):
    def get_descendants(self, *args, **kwargs):
        """
        Alias to `mptt.managers.TreeManager.get_queryset_descendants`.
        """
        return self.model._tree_manager.get_queryset_descendants(self, *args, **kwargs)

    get_descendants.queryset_only = True

    def get_ancestors(self, *args, **kwargs):
        """
        Alias to `mptt.managers.TreeManager.get_queryset_ancestors`.
        """
        return self.model._tree_manager.get_queryset_ancestors(self, *args, **kwargs)

    get_ancestors.queryset_only = True

#    def get_cached_trees(self):
#        """
#        Alias to `mptt.utils.get_cached_trees`.
#        """
#        return utils.get_cached_trees(self)
