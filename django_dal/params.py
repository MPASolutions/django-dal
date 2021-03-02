import importlib
from collections import OrderedDict
from contextvars import *

from django.conf import settings
from django.utils.functional import LazyObject


class ContextParam:

    def __init__(self, name, type, description, default=None):
        self.name = name
        self.type = type  # may be class or list of classes, e.g. AnonymousUser is not subclass of User
        self.description = description
        self.default = default


class ContextParams:
    #: List of ContextParam instances
    params = []

    def __init__(self):
        self.__dict__['vars'] = {}
        for param in self.params:
            self.__dict__['vars'][param.name] = ContextVar(param.name, default=param.default)

    def __getattr__(self, name):
        return self.__dict__['vars'][name].get()

    def __setattr__(self, name, value):
        self.__dict__['vars'][name].set(value)

    def _get_param(self, name):
        a = self.params
        b = [i.name for i in self.params]
        for param in self.params:
            if param.name == name:
                return param
        raise Exception('Param {} does not exist in ContextParams'.format(name))

    def set_defaults(self):
        """
        Reset to default values
        :return:
        """
        for name, variable in self.__dict__['vars'].items():
            param = self._get_param(name)
            self.__dict__['vars'][name].set(param.default)

    def set_to_none(self):
        """
        Set all params to None
        :return:
        """
        for name, variable in self.__dict__['vars'].items():
            self.__dict__['vars'][name].set(None)

    def get_from_request(self, request):
        return {}

    def set_from_request(self, request):
        self.set(self.get_from_request(request))

    def set(self, values):
        self.set_to_none()
        for name, value in values.items():
            param = self._get_param(name)  # raises exception if does not exist
            # e.g. request.user in middleware may LazyObject
            if isinstance(value, LazyObject) and hasattr(value, '_wrapped'):
                value = value._wrapped
            if value is not None and not isinstance(value, param.type):
                raise Exception(
                    'Trying to set ContextParam {} to value {} of type {} which does not match param type {}'.format(
                        name, value, type(value), param.type))
            self.__dict__['vars'][name].set(value)

    def get(self):
        vars = OrderedDict()
        for param in self.params:
            value = self.__dict__['vars'][param.name].get()
            vars[param.name] = value
        return vars

    @staticmethod
    def get_user_group(user):
        if user is None:
            return None
        groups = user.groups.get_queryset()
        if len(groups) == 0:
            return None
        elif len(groups) == 1:
            return groups[0]
        raise Exception('User {} in more groups: {}'.format(user.username, groups))

    # this is run in context copy
    @staticmethod
    def run_in_context(*args, **kwargs):
        # set params in context copy
        params = kwargs.pop('__context_params_to_set__')
        cxpr.set(params)
        function = kwargs.pop('__callable_to_run__')
        return function(*args, **kwargs)

    def run(self, params, function, *args, **kwargs):
        context = copy_context()
        kwargs['__context_params_to_set__'] = params
        kwargs['__callable_to_run__'] = function
        return context.run(self.run_in_context, *args, **kwargs)

    def __str__(self):
        vars = self.get_list()
        for name, value in self.get():
            vars.append('{}={}'.format(name, value))
        return '{}({})'.format(self.__class__.__name__, ', '.join(vars))

    def __repr__(self):
        return self.__str__()

    def describe(self):
        vars = []
        for param in self.params:
            value = self.__dict__['vars'][param.name].get()
            vars.append('{}: {} ({}, type={}, default={})'.format(param.name, value, param.description, param.type,
                                                                  param.default))
        return '\n'.join(vars)


# Proxy pattern from
# http://jtushman.github.io/blog/2014/05/02/module-properties/
class ModuleProperty(object):

    def __init__(self, get_property_function):
        self.function = get_property_function

    def __getattr__(self, name):
        # execute function and get its attribute
        return getattr(self.function(), name)

    def __str__(self):
        return str([(i.name, getattr(self, i.name)) for i in self.params])


@ModuleProperty
def cxpr():
    return get_context_params()


# Context params global instance
context_params = None


def get_context_params():
    global context_params
    if not context_params:
        # import project
        if hasattr(settings, 'CONTEXT_PARAMS'):
            path = settings.CONTEXT_PARAMS.split('.')
            module = importlib.import_module('.'.join(path[:-1]))
            cls = getattr(module, path[-1])
            context_params = cls()
        else:
            context_params = ContextParams()
    return context_params
