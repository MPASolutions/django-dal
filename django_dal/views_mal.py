import posixpath
import urllib

import os
import re
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.views.generic import View
from django.views.static import serve


class BaseSendFileView(View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        _path = self.kwargs.get('path', None)
        if _path in ['', None]:
            return Http404('Path is not sended')
        else:
            filepath = _path #= os.path.join(settings.MEDIA_URL, _path)

        # custom rule (to increase in future)
        for rule in settings.DJANGO_DAL_RULES:
            if 'regex' in rule:
                pattern = re.compile(rule['regex'])
                if pattern.match(filepath):
                    return self.serve(filepath)

        # standard
        if not self.request.user.is_authenticated:
            return HttpResponse('Unauthorized', status=401)

        filepath, stable = self.clear_path(filepath)

        # Clean up given path to only allow serving files below document_root.
        if filepath and not stable:
            return HttpResponseRedirect(filepath)

        # check permissions
        _found = False
        for ct in ContentType.objects.all():
            Model = ct.model_class()
            if Model is not None and request.user.has_perm('{}.view_{}'.format(Model._meta.app_label,
                                                                               Model._meta.model_name)):
                for field in Model._meta.fields:
                    if hasattr(field, 'upload_to'):
                        if Model.objects.filter(**{field.name: _path}).exists():
                            _found = True

        if not _found:
            raise PermissionDenied('File not found or user has no enought permissions')

        return self.serve(filepath)

    def serve(self, filepath):
        return serve(self.request,
                     filepath,
                     document_root=settings.MEDIA_ROOT,
                     show_indexes=False)

    def clear_path(self, filepath):
        filepath = posixpath.normpath(urllib.parse.unquote(filepath))
        filepath = filepath.lstrip('/')
        newpath = ''
        for part in filepath.split('/'):
            if not part:
                # Strip empty path components.
                continue
            drive, part = os.path.splitdrive(part)
            head, part = os.path.split(part)
            if part in (os.curdir, os.pardir):
                # Strip '.' and '..' in filepath.
                continue
            newpath = os.path.join(newpath, part).replace('\\', '/')
        return newpath, filepath == newpath

    def identify_path(self, filepath, re_path):
        regex = re.compile(re_path, re.I)
        match = regex.match(str(filepath))
        return bool(match)
