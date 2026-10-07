from dataclasses import dataclass
from typing import Protocol

from fastapi import HTTPException, Request, status


@dataclass(frozen=True)
class AuthenticatedCustomer:
    customer_id: str


class CustomerContextProvider(Protocol):
    def resolve(self, request: Request) -> AuthenticatedCustomer | None: ...


def get_authenticated_customer(request: Request) -> AuthenticatedCustomer:
    provider: CustomerContextProvider | None = getattr(
        request.app.state, "customer_context_provider", None
    )
    customer = provider.resolve(request) if provider is not None else None
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    return customer