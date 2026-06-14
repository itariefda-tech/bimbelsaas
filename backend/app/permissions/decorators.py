from collections.abc import Callable
from functools import wraps

from flask import g, request

from app.common.errors import AuthenticationError
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.services.auth_service import AuthService
from app.services.authorization_service import AuthorizationService

TargetResolver = Callable[..., AuthorizationTarget]


def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        g.principal = _authenticate_request()
        return view(*args, **kwargs)

    return wrapped


def require_permission(
    permission: Permission,
    target_resolver: TargetResolver,
):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            principal = _authenticate_request()
            target = target_resolver(*args, **kwargs)
            AuthorizationService.require(principal, permission, target)
            g.principal = principal
            return view(*args, **kwargs)

        return wrapped

    return decorator


def _authenticate_request() -> Principal:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError()
    return AuthService().authenticate_access_token(token)
