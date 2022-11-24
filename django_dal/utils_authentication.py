# -*- coding: utf-8 -*-

import binascii

import base64
from django.contrib.auth import login

from django_dal.params import get_context_params


def get_basic_auth(request):
    auth = None
    userid = None
    password = None
    if 'Authorization' in request.META:
        auth = request.META['Authorization']
    elif 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION']

    if auth is not None:
        auth = auth.encode('iso-8859-1')

        auth = auth.split()

        msg = None
        if not auth or auth[0].lower() != b'basic':
            msg = 'Invalid basic header.'

        if len(auth) == 1:
            msg = 'Invalid basic header. No credentials provided.'
        elif len(auth) > 2:
            msg = 'Invalid basic header. Credentials string should not contain spaces.'

        try:
            auth_parts = base64.b64decode(auth[1]).decode('iso-8859-1').partition(':')
        except (TypeError, UnicodeDecodeError, binascii.Error):
            msg = 'Invalid basic header. Credentials not correctly base64 encoded.'

        if msg is None:
            userid, password = auth_parts[0], auth_parts[2]
    else:
        msg = 'Invalid header, no autentication provided.'

    return userid, password, msg


def authorize(request):
    if not request.user.is_authenticated:
        user, password, msg = get_basic_auth(request)
        if msg is not None:
            return False, msg
        login(request, user)
        if not request.user.is_authenticated:
            return False, 'User is not authenticated'

    context_params = get_context_params()
    context_params.set_to_none()
    context_params.set_from_request(request)
    context_params.set_from_request_post(request)

    return True, None
