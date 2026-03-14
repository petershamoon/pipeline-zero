"""Microsoft Entra JWT validation and claim mapping."""
from __future__ import annotations

from dataclasses import dataclass

import httpx
from jose import jwt
from jose.exceptions import JOSEError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.enums import UserRole
from app.models.user import User


class EntraAuthError(RuntimeError):
    pass


@dataclass(slots=True)
class EntraPrincipal:
    object_id: str
    email: str
    display_name: str
    role: UserRole


def _issuer(settings: Settings) -> str:
    return f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}/v2.0"


def _jwks_url(settings: Settings) -> str:
    return f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}/discovery/v2.0/keys"


def _map_role(claims: dict) -> UserRole:
    role_values = claims.get("roles", [])
    if isinstance(role_values, str):
        role_values = [role_values]

    if "ContractFlow.SuperAdmin" in role_values:
        return UserRole.SUPER_ADMIN
    if "ContractFlow.Admin" in role_values:
        return UserRole.ADMIN
    if "ContractFlow.Approver" in role_values:
        return UserRole.APPROVER
    if "ContractFlow.Contributor" in role_values:
        return UserRole.CONTRIBUTOR
    return UserRole.VIEWER


async def validate_bearer_token(token: str, settings: Settings) -> EntraPrincipal:
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JOSEError as exc:
        raise EntraAuthError("Invalid token header") from exc

    key_id = unverified_header.get("kid")
    if not key_id:
        raise EntraAuthError("Token missing key id")

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(_jwks_url(settings))
        response.raise_for_status()
        keys = response.json().get("keys", [])

    signing_key = next((key for key in keys if key.get("kid") == key_id), None)
    if signing_key is None:
        raise EntraAuthError("Signing key not found")

    try:
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.ENTRA_AUDIENCE,
            issuer=_issuer(settings),
        )
    except JOSEError as exc:
        raise EntraAuthError("Token validation failed") from exc

    object_id = claims.get("oid") or claims.get("sub")
    if not object_id:
        raise EntraAuthError("Token missing object id")

    email = claims.get("preferred_username") or claims.get("upn") or f"{object_id}@entra.local"
    display_name = claims.get("name") or email

    return EntraPrincipal(
        object_id=str(object_id),
        email=str(email),
        display_name=str(display_name),
        role=_map_role(claims),
    )


async def upsert_entra_user(db: AsyncSession, principal: EntraPrincipal) -> User:
    user = (
        await db.execute(select(User).where(User.entra_object_id == principal.object_id).limit(1))
    ).scalar_one_or_none()

    if user is None:
        user = User(
            email=principal.email,
            display_name=principal.display_name,
            role=principal.role,
            entra_object_id=principal.object_id,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        return user

    user.email = principal.email
    user.display_name = principal.display_name
    user.role = principal.role
    user.is_active = True
    await db.flush()
    return user
