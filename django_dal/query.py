from django.db.models.query import QuerySet
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
        return super().update(objs, fields, batch_size=batch_size)


class DALTreeQuerySet(DALQuerySet):
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

    def get_cached_trees(self):
        """
        Alias to `mptt.utils.get_cached_trees`.
        """
        return utils.get_cached_trees(self)
