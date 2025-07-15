import importlib
import json
from collections import OrderedDict
from contextvars import ContextVar, copy_context
from hashlib import md5

from django.conf import settings
from django.db import models
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
        self.__dict__["vars"] = {}
        for param in self.params:
            self.__dict__["vars"][param.name] = ContextVar(param.name, default=param.default)

    def __getattr__(self, name):
        try:
            return self.__dict__["vars"][name].get()
        except KeyError:
            raise AttributeError

    def __setattr__(self, name, value):
        self.__dict__["vars"][name].set(value)

    def _get_param(self, name):
        for param in self.params:
            if param.name == name:
                return param
        raise Exception("Param {} does not exist in ContextParams".format(name))

    def set_defaults(self):
        """
        Reset to default values
        :return:
        """
        for name, variable in self.__dict__["vars"].items():
            param = self._get_param(name)
            self.__dict__["vars"][name].set(param.default)

    def set_to_none(self):
        """
        Set all params to None
        :return:
        """
        for name, variable in self.__dict__["vars"].items():
            self.__dict__["vars"][name].set(None)

    def get_from_request(self, request):
        return {}

    def set_from_request(self, request):
        self.set(self.get_from_request(request))

    def get_from_request_post(self, request):
        return {}

    def set_from_request_post(self, request):
        self.set_post(self.get_from_request_post(request))

    def _set(self, values):
        for name, value in values.items():
            param = self._get_param(name)  # raises exception if does not exist
            # e.g. request.user in middleware may LazyObject
            if isinstance(value, LazyObject) and hasattr(value, "_wrapped"):
                value = value._wrapped
            if value is not None and not isinstance(value, param.type):
                raise Exception(
                    "Trying to set ContextParam {} to value {} of type {} which does not match param type {}".format(
                        name, value, type(value), param.type
                    )
                )
            self.__dict__["vars"][name].set(value)

    def set(self, values):
        self.set_to_none()
        self._set(values)

    def set_post(self, values):
        self._set(values)

    def get(self):
        vars = OrderedDict()
        for param in self.params:
            value = self.__dict__["vars"][param.name].get()
            vars[param.name] = value
        return vars

    def get_user(self):
        """
        If it has Django User defined get current user, AnonymousUser otherwise
        Returns: Django User
        """
        from django.contrib.auth.models import AbstractUser, AnonymousUser

        user = None
        for param in self.params:
            value = self.__dict__["vars"][param.name].get()
            if issubclass(param.type, AbstractUser) and value is not None:
                if user is not None:
                    raise Exception("Cannot get cxpr user, multiple User params.")
                user = value
        return user if user else AnonymousUser()

    @staticmethod
    def get_user_group(user):
        if user is None:
            return None
        groups = user.groups.get_queryset()
        if len(groups) == 0:
            return None
        elif len(groups) == 1:
            return groups[0]
        raise Exception("User {} in more groups: {}".format(user.username, groups))

    # this is run in context copy
    @staticmethod
    def run_in_context(*args, **kwargs):
        # set params in context copy
        params = kwargs.pop("__context_params_to_set__")
        cxpr.set(params)
        function = kwargs.pop("__callable_to_run__")
        return function(*args, **kwargs)

    def run(self, params, function, *args, **kwargs):
        context = copy_context()
        kwargs["__context_params_to_set__"] = params
        kwargs["__callable_to_run__"] = function
        return context.run(self.run_in_context, *args, **kwargs)

    def __str__(self):
        # vars = self.get_list()
        var_list = []
        for name, value in self.get().items():
            var_list.append("{}={}".format(name, value))
        return "{}({})".format(self.__class__.__name__, ", ".join(var_list))

    def __repr__(self):
        return self.__str__()

    def get_checksum(self):
        md = md5()
        for param in self.params:
            value = self.__dict__["vars"][param.name].get()
            if isinstance(value, (int, str, type(None))):
                string = str(value)
            elif isinstance(value, models.Model):
                string = str(value.pk)
            else:
                raise Exception("Cxpr checksum unsupported type: {}".format(type(value)))
            md.update(string.encode("utf-8"))
        return md.hexdigest()

    def describe(self):
        variables = []
        for param in self.params:
            value = self.__dict__["vars"][param.name].get()
            variables.append(
                "{}: {} ({}, type={}, default={})".format(
                    param.name, value, param.description, param.type, param.default
                )
            )

        return "\n".join(variables)

    @staticmethod
    def get_class_path(klass):
        """Return the full name of the given object using its module and qualified class names."""
        # Ref: https://stackoverflow.com/a/66508248/
        module_name, class_name = klass.__module__, klass.__qualname__
        if module_name in (None, str.__class__.__module__):
            return class_name
        return module_name + "." + class_name

    def get_values_json_str(self):
        """
        Returns:
            JSON string which may be parsed by parse_values_json_str()
        """
        variables = []
        for param in self.params:
            value = self.__dict__["vars"][param.name].get()
            if isinstance(value, models.Model):
                value = value.pk
            variables.append({"name": param.name, "value": value})
        return json.dumps(variables, sort_keys=True)

    @staticmethod
    def get_class(class_path):
        module_path, name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, name)

    def set_values_json_str(self, json_str):
        """
        Returns:
            Parse and set JSON string produced by get_values_json_str()
        """
        variables = json.loads(json_str)
        values = {}
        for variable in variables:
            param = self._get_param(variable["name"])
            value = variable["value"]
            if value is not None and issubclass(param.type, models.Model):
                value = param.type.objects.get(pk=value)
            values[variable["name"]] = value
        self.set(values)


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
        if hasattr(settings, "CONTEXT_PARAMS"):
            path = settings.CONTEXT_PARAMS.split(".")
            module = importlib.import_module(".".join(path[:-1]))
            cls = getattr(module, path[-1])
            context_params = cls()
        else:
            context_params = ContextParams()
    return context_params
