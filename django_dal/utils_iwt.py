import base64
import datetime
import fnmatch
import json
from datetime import timezone
from pathlib import Path
from typing import Optional, Tuple

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, BadRequest


def read_file_or_str_bytes(path_or_str):
    """
    Reads the content of a file or a bytes string.

    This function takes a path or a bytes string as input. If the input is a Path object
    and points to a valid file, it reads and returns the content of the file as bytes.
    If the input is already a bytes string, it simply returns the input as is. If the
    input is neither a valid file nor a bytes string, it raises an ImproperlyConfigured
    exception.

    :param path_or_str: The path to the file or a bytes string.
    :type path_or_str: pathlib.Path or bytes
    :return: The content of the file or the bytes string.
    :rtype: bytes
    :raises ImproperlyConfigured: If the input is not a valid file or a bytes string.
    """
    if path_or_str is not None:
        if isinstance(path_or_str, Path):
            if path_or_str.is_file():
                return path_or_str.read_bytes()
            else:
                raise ImproperlyConfigured('File path configured in settings not found: {}'.format(path_or_str))
        elif isinstance(path_or_str, bytes):
            return path_or_str
        else:
            raise ImproperlyConfigured('No path or bytes string configured in settings: {}'.format(path_or_str))
    return None


def orginal_exception_msg(e):
    return "due to {}: {}".format(e.__class__.__name__, str(e))

def wildcards_get(dictionary, key):
    """
    Get values from dictionary with wildcards in keys.

    Support for Unix shell-style wildcards, which are not the same as regular expressions
    The special characters used in shell-style wildcards are:
    * matches everything
    ? matches any single character
    [seq] matches any character in seq
    [!seq] matches any character not in seq

    :param dictionary: the dictionary from which to get the value
    :param key: the key of the value to be returned (without wildcards)
    :return: a dictionary value
    """
    if key is not None:
        return dictionary.get(key, next((v for k, v in dictionary.items() if fnmatch.fnmatch(key, k)), None))
    return None

def encode_jwt(request, audience, issuer=None, expiration=30, extra_payload=None, jwt_required=False, debug=False):
    """
    Encode JWT authorization with private key and optional passphrase
    adds remote user and session to jwt payload

    TO GENERATE A NEW KEY PAIR
    ssh-keygen -t rsa -b 4096 -m PEM -f jwtRS256.key
    Note: add passphrase
    openssl rsa -in jwtRS256.key -pubout -outform PEM -out jwtRS256.key.pub
    cat jwtRS256.key
    cat jwtRS256.key.pub

    Settings configuration example (gerally configured only in issuers projects settings):
    DJANGO_DAL_RSA_KEYS = {
        'local': {
            'private': 'my loacl private kwy',  # pathlib.Path or bstr key
            'passphrase': 'my local passphrase',  # optional bytestr or None
        },
    }

    :param request:
    :param audience: required audience urn (generally the proxy host)
    :param issuer: optional issuer urn, deafult is request.get_host()
    :param expiration: jwt expration time in seconds, default 30
    :param extra_payload: optional dict of data to add in jwt payload
    :param jwt_required: deafult False, denotes if JWT autentication is requierd,
    :param debug: raise orginal expetion message when unable to encode JWT
    if True rasie ImproperlyConfigured if not private key configured in settings: DJANGO_DAL_RSA_KEYS.local.private
    :return:
    """
    pem_bytes = read_file_or_str_bytes(
        getattr(settings, 'DJANGO_DAL_RSA_KEYS', {}).get('local', {}).get('private')
    )
    if jwt_required is True and pem_bytes is None:
        raise ImproperlyConfigured(
            'No RSA key found in settings: DJANGO_DAL_RSA_KEYS.local.private'
        )

    passphrase = read_file_or_str_bytes(
        getattr(settings, 'DJANGO_DAL_RSA_KEYS', {}).get('local', {}).get('passphrase')
    )  # optional

    if pem_bytes is not None:
        try:
            private_key = serialization.load_pem_private_key(
                pem_bytes, password=passphrase, backend=default_backend()
            )
            encoded_jwt = jwt.encode(
                {
                    'exp': datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(seconds=expiration),
                    'nbf': datetime.datetime.now(tz=timezone.utc),  # not before
                    # https://en.wikipedia.org/wiki/Uniform_Resource_Name
                    'iss': 'urn:{}'.format(issuer or request.get_host()),  # issuer
                    'aud': 'urn:{}'.format(audience),  # audience urlparse(host).netloc
                    'iat': datetime.datetime.now(tz=timezone.utc),
                    'remote_userid': request.user.id if request.user else None,
                    'remote_username': request.user.username if request.user else None,
                } | dict(request.session or {}) | (extra_payload or {}),
                private_key,
                algorithm="RS512"
            )
            return encoded_jwt
        except Exception as e:
            # molto probabilmente chiave privata non valida
            raise ImproperlyConfigured(
                "Unable to ecode JWT token" + (orginal_exception_msg(e) if debug else '')
            )

    return None


def decode_jwt(
    request, jwt_required=False, debug=False
) -> Tuple[bool, Optional[dict], str]:
    """
    Try to decode JWT if sent in request data and audience project is configured to receive a JWT from the given issuer

    Settings configuration example (usually configured only in audience project settings with list of supported isssuers):
    DJANGO_DAL_RSA_KEYS = {
        'remotes': {
            'public': {
                'biogardgis.test.mpasol.it': 'public remote biogard',  # pathlib.Path or bstr key
                # 'urn_issuere2': 'public remote issuere2'  # pathlib.Path or bstr key
            }
        }
    }

    :param request:
    :param jwt_required: default False, denotes if JWT autentication is required for given request
    if False return Error only when JWT is sent in request data and audience project is configured to receive JWT from the given issuer
    if True return Error in any case JWT cannot be authorized succefully, or settings has no issuer public key configured
    :param debug: return orginal expetion message when unable to decode JWT
    return: A tuple containing a boolean indicating if the decoding was successful, the
        payload of the decoded JWT, or None if the JWT could not be decoded, and a
        string error message.
    :rtype: tuple (bool, dict or None, str)
    """
    jwt_payload = None
    # performs cehcks to verify that the authentication with JWT can be done
    # errors are to be returned only if jwt_requireqd=True, otherwise fail silently (default)
    try:
        if not (request.body and isinstance(request.body, bytes)):
            raise BadRequest('No bytes string found in request data')

        # https://jwt.io/introduction
        # JWT typically looks like the following: xxxxx.yyyyy.zzzzz
        # The header (xxxxx) typically consists of two parts: the type of the token, which is JWT,
        # and the signing algorithm being used, such as HMAC SHA256 or RSA.
        # {
        #   "alg": "HS256",
        #   "typ": "JWT"
        # }
        if json.loads(base64.b64decode(request.body.split(b'.')[0]))['typ'] != 'JWT':
            raise BadRequest('No bytes string with typ:JWT found in request data')

        issuer = request.headers.get('Referer')
        if issuer is None:
            raise BadRequest('No Referer found in request headers')

        public_key = read_file_or_str_bytes(wildcards_get(
            getattr(settings, 'DJANGO_DAL_RSA_KEYS', {}).get('remotes', {}).get('public', {}),
            issuer
        ))
        if public_key is None:
            raise ImproperlyConfigured(
                'No RSA key found in settings: DJANGO_DAL_RSA_KEYS.remotes.public.{}'.format(issuer)
            )

    except Exception as e:
        # BadRequest: non post data or required header not sent
        # ImproperlyConfigured: non RSA key configured in audience (client) settings
        # else: broken with generic Exception on body parsing to check if JWT is used
        if jwt_required is True:
            return (
                False,
                jwt_payload,
                str(e) if isinstance(
                    e, (BadRequest, ImproperlyConfigured)
                ) else "Unable to find JWT in request data" + (orginal_exception_msg(e) if debug else '')
            )
        else:
            # OK, request without JWT authentication or issuer project not configured to use it
            return True, jwt_payload, None

    # at this point we ensured the JWT was sent and the receiver is part of the audience of that issuer,
    # therefore if it fails we alwasy return an authentication error and an error message (exception)
    try:
        jwt_payload = jwt.decode(
            request.body,
            public_key,
            issuer="urn:{}".format(request.headers.get('Referer')),
            audience='urn:{}'.format(request.get_host()),
            algorithms="RS512",
            options={"require": ["exp", "nbf", "iss", "aud", "iat", "remote_userid", "remote_username"]}
        )
    except jwt.ExpiredSignatureError:
        return False, jwt_payload, "JWT token expired"
    except jwt.InvalidIssuerError:
        return False, jwt_payload, "JWT invalid issuer"
    except jwt.InvalidAudienceError:
        return False, jwt_payload, "JWT invalid audience"
    except jwt.ImmatureSignatureError:
        return False, jwt_payload, "JWT token is not yet valid (nbf)"
    except jwt.InvalidTokenError:  # Base exception when decode() fails on a token
        return False, jwt_payload, "JWT invalid token"
    except Exception as e:
        # with wrog public key does not raise jwt specific exception
        return False, jwt_payload, "Unable to decode JWT token" + (orginal_exception_msg(e) if debug else '')

    # OK, valid JWT authentication
    return True, jwt_payload, None
