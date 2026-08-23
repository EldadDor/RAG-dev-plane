"""Environment-neutral authenticated principal resolution."""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request

from app.config import Settings, get_settings


@dataclass(frozen=True)
class Principal:
    subject: str
    display_name: str
    email: str | None = None


def get_principal(request: Request, settings: Settings = Depends(get_settings)) -> Principal:
    if settings.auth_mode == "local":
        return Principal(
            subject=settings.local_subject,
            display_name=settings.local_display_name,
            email=settings.local_email,
        )

    subject = request.headers.get(settings.chat_identity_header)
    if not subject:
        raise HTTPException(status_code=401, detail="Trusted gateway identity is required")
    return Principal(
        subject=subject,
        display_name=request.headers.get(settings.chat_identity_name_header, subject),
        email=request.headers.get(settings.chat_identity_email_header),
    )
