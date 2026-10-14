from hashlib import sha256
import hmac

from fastapi import Depends, HTTPException, Request, status

from simple_bank.security.context import AuthenticatedCustomer, get_authenticated_customer


CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"


def require_same_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin is None:
        return
    settings = request.app.state.settings
    expected = settings.public_origin or f"{request.url.scheme}://{request.url.netloc}"
    if not hmac.compare_digest(origin.rstrip("/"), expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The request origin is not allowed.",
        )


def require_session_csrf(
    request: Request,
    customer: AuthenticatedCustomer = Depends(get_authenticated_customer),
) -> AuthenticatedCustomer:
    require_same_origin(request)
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")
    header_token = request.headers.get(CSRF_HEADER_NAME, "")
    if (
        not cookie_token
        or not header_token
        or not hmac.compare_digest(cookie_token, header_token)
        or not hmac.compare_digest(
            sha256(cookie_token.encode("utf-8")).hexdigest(),
            customer.csrf_token_digest,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A valid CSRF token is required.",
        )
    return customer