import base64
import binascii

from django.contrib.auth import authenticate, login

from django_dal.params import get_context_params
from django_dal.utils_iwt import decode_jwt


def get_basic_auth(request):
    auth = None
    userid = None
    password = None
    if "Authorization" in request.META:
        auth = request.META["Authorization"]
    elif "HTTP_AUTHORIZATION" in request.META:
        auth = request.META["HTTP_AUTHORIZATION"]

    if auth is not None:
        auth = auth.encode("iso-8859-1")

        auth = auth.split()

        msg = None
        if not auth or auth[0].lower() != b"basic":
            msg = "Invalid basic header."

        if len(auth) == 1:
            msg = "Invalid basic header. No credentials provided."
        elif len(auth) > 2:
            msg = "Invalid basic header. Credentials string should not contain spaces."

        try:
            auth_parts = base64.b64decode(auth[1]).decode("iso-8859-1").partition(":")
        except (TypeError, UnicodeDecodeError, binascii.Error):
            msg = "Invalid basic header. Credentials not correctly base64 encoded."

        if msg is None:
            userid, password = auth_parts[0], auth_parts[2]
    else:
        msg = "Invalid header, no autentication provided."

    return userid, password, msg


def authorize(request):
    if not request.user.is_authenticated:

        # check JWT
        jwt_authorized, jwt_payload, msg = decode_jwt(request, jwt_required=False)
        # with jwt_required=False it returns jwt_authorized as False only if really fails to decode/expired/invalid
        # if no JWT was sent in the request or the audience is not configured to receive it, it returns
        # anyway jwt_authorized True (but jwt_payload is None)
        if jwt_authorized is False:
            return False, msg

        username, password, msg = get_basic_auth(request)
        if msg is not None:
            return False, msg

        user = authenticate(username=username, password=password)
        if not user or not user.is_active:
            return False, "User is not active"

        login(request, user)

        if not request.user.is_authenticated:
            return False, "User is not authenticated"

        # add the issuer session to the new session (without overwriting the orginal authenticaiton keys)
        # if it had been done earlier (where jwt_authorized is checked)
        # it would have been overwritten by authenticate/login
        # so I have to do it here at the end with the caution not to overwrite the keys of the orginal authentication
        if jwt_payload is not None:
            request.session.update(
                {
                    k: v
                    for k, v in jwt_payload.items()
                    if k not in ["_auth_user_id", "_auth_user_backend", "_auth_user_hash"]
                }
            )

    context_params = get_context_params()
    context_params.set_to_none()
    context_params.set_from_request(request)
    context_params.set_from_request_post(request)

    return True, None
