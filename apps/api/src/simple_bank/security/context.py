from dataclasses import dataclass
from hashlib import sha256
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from fastapi import HTTPException, Request, status

from simple_bank.domain.auth_repository import AuthRepository
from simple_bank.settings import Settings


@dataclass(frozen=True)
class AuthenticatedCustomer:
    customer_id: str
    session_id: str | None = None
    display_name: str = ""
    email_verified: bool = False
    mobile_verified: bool = False
    csrf_token_digest: str = ""

    @property
    def transfer_eligible(self) -> bool:
        return self.email_verified or self.mobile_verified


class CustomerContextProvider(Protocol):
    def resolve(self, request: Request) -> AuthenticatedCustomer | None: ...

    def rotate_csrf_token_digest(self, session_id: str, token_digest: str) -> None: ...


class DatabaseCustomerContextProvider:
    def __init__(
        self,
        repository: AuthRepository,
        settings: Settings,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._clock = clock or (lambda: datetime.now(UTC))

    def resolve(self, request: Request) -> AuthenticatedCustomer | None:
        raw_token = request.cookies.get(self._settings.session_cookie_name)
        if not raw_token:
            return None
        principal = self._repository.resolve_session(
            sha256(raw_token.encode("utf-8")).hexdigest(), self._clock().astimezone(UTC)
        )
        if principal is None:
            return None
        return AuthenticatedCustomer(
            customer_id=principal.customer_id,
            session_id=principal.session_id,
            display_name=principal.display_name,
            email_verified=principal.email_verified,
            mobile_verified=principal.mobile_verified,
            csrf_token_digest=principal.csrf_token_digest,
        )

    def rotate_csrf_token_digest(self, session_id: str, token_digest: str) -> None:
        self._repository.update_session_csrf_digest(session_id, token_digest)


def get_optional_authenticated_customer(request: Request) -> AuthenticatedCustomer | None:
    provider: CustomerContextProvider | None = getattr(
        request.app.state, "customer_context_provider", None
    )
    return provider.resolve(request) if provider is not None else None


def get_authenticated_customer(request: Request) -> AuthenticatedCustomer:
    customer = get_optional_authenticated_customer(request)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    return customer