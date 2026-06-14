import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import jwt
from flask import current_app

from app.common.errors import AuthenticationError


class TokenService:
    @staticmethod
    def hash_jti(jti: str) -> str:
        return hashlib.sha256(jti.encode("utf-8")).hexdigest()

    @staticmethod
    def create_access_token(*, user_id: UUID, session_id: UUID) -> str:
        return TokenService._encode(
            user_id=user_id,
            session_id=session_id,
            token_type="access",
            expires_delta=current_app.config["JWT_ACCESS_TTL"],
        )[0]

    @staticmethod
    def create_refresh_token(*, user_id: UUID, session_id: UUID) -> tuple[str, str]:
        return TokenService._encode(
            user_id=user_id,
            session_id=session_id,
            token_type="refresh",
            expires_delta=current_app.config["JWT_REFRESH_TTL"],
        )

    @staticmethod
    def decode(token: str, *, expected_type: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=[current_app.config["JWT_ALGORITHM"]],
                options={"require": ["sub", "sid", "type", "jti", "iat", "exp"]},
            )
        except jwt.ExpiredSignatureError as error:
            raise AuthenticationError(
                "The token has expired.",
                "token_expired",
            ) from error
        except jwt.InvalidTokenError as error:
            raise AuthenticationError(
                "The token is invalid.",
                "invalid_token",
            ) from error

        if payload["type"] != expected_type:
            raise AuthenticationError(
                "The token type is invalid for this operation.",
                "invalid_token_type",
            )
        return payload

    @staticmethod
    def _encode(
        *,
        user_id: UUID,
        session_id: UUID,
        token_type: str,
        expires_delta,
    ) -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        jti = str(uuid4())
        payload = {
            "sub": str(user_id),
            "sid": str(session_id),
            "type": token_type,
            "jti": jti,
            "iat": now,
            "exp": now + expires_delta,
        }
        token = jwt.encode(
            payload,
            current_app.config["SECRET_KEY"],
            algorithm=current_app.config["JWT_ALGORITHM"],
        )
        return token, jti

