from hashlib import sha256
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from simple_bank.api.schemas.auth import (
	ContactVerificationConfirmRequest,
	ContactVerificationRequest,
	ContactVerificationRequestResponse,
	ContactVerificationResponse,
	LoginRequest,
	LoginResponse,
	PasswordResetConfirmRequest,
	PasswordResetRequest,
	RegistrationRequest,
	RegistrationResponse,
	SessionStatusResponse,
)
from simple_bank.api.security.csrf import (
	CSRF_COOKIE_NAME,
	require_same_origin,
	require_session_csrf,
)
from simple_bank.domain.account_numbers import mask_account_number
from simple_bank.domain.auth import ContactChannel, RegistrationCommand
from simple_bank.domain.auth_errors import InvalidOrExpiredChallenge
from simple_bank.security.context import (
	AuthenticatedCustomer,
	get_optional_authenticated_customer,
)
from simple_bank.services.auth_service import CustomerAuthService
from simple_bank.settings import Settings


router = APIRouter()


def get_auth_service(request: Request) -> CustomerAuthService:
	service: CustomerAuthService | None = getattr(request.app.state, "auth_service", None)
	if service is None:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="Authentication service is not configured.",
		)
	return service


def get_settings(request: Request) -> Settings:
	return request.app.state.settings


def _set_csrf_cookie(response: Response, token: str, settings: Settings) -> None:
	response.set_cookie(
		key=CSRF_COOKIE_NAME,
		value=token,
		httponly=False,
		secure=settings.session_cookie_secure,
		samesite=settings.session_cookie_samesite,
		path="/",
	)


@router.post("/auth/register", response_model=RegistrationResponse, status_code=201)
def register_customer(
	payload: RegistrationRequest,
	service: CustomerAuthService = Depends(get_auth_service),
	_origin_ok: None = Depends(require_same_origin),
) -> RegistrationResponse:
	result = service.register(
		RegistrationCommand(
			name=payload.name,
			email=payload.email,
			mobile_number=payload.mobile_number,
			username=payload.username,
			password=payload.password,
			account_number_suffix=payload.account_number_suffix,
		)
	)
	return RegistrationResponse(
		customer_id=result.customer_id,
		account_number=mask_account_number(result.account.account_number),
		account_type=result.account.account_type,
		status=result.account.status,
		transfer_eligible=result.transfer_eligible,
	)


@router.post("/auth/login", response_model=LoginResponse)
def login(
	payload: LoginRequest,
	response: Response,
	service: CustomerAuthService = Depends(get_auth_service),
	settings: Settings = Depends(get_settings),
	_origin_ok: None = Depends(require_same_origin),
) -> LoginResponse:
	grant = service.login(payload.username, payload.password)
	response.set_cookie(
		key=settings.session_cookie_name,
		value=grant.session_token,
		httponly=True,
		secure=settings.session_cookie_secure,
		samesite=settings.session_cookie_samesite,
		max_age=settings.session_max_age_seconds,
		path="/",
	)
	_set_csrf_cookie(response, grant.csrf_token, settings)
	profile = service.profile_for_customer(grant.customer_id)
	return LoginResponse(
		customer_id=grant.customer_id,
		csrf_token=grant.csrf_token,
		transfer_eligible=profile.transfer_eligible,
	)


@router.get("/auth/session", response_model=SessionStatusResponse)
def session_status(
	request: Request,
	response: Response,
	settings: Settings = Depends(get_settings),
	customer: AuthenticatedCustomer | None = Depends(get_optional_authenticated_customer),
) -> SessionStatusResponse:
	csrf_token = request.cookies.get(CSRF_COOKIE_NAME, "")
	if customer is not None and (
		not csrf_token
		or sha256(csrf_token.encode("utf-8")).hexdigest() != customer.csrf_token_digest
	):
		csrf_token = secrets.token_urlsafe(32)
		provider = getattr(request.app.state, "customer_context_provider", None)
		if provider is not None and customer.session_id is not None:
			provider.rotate_csrf_token_digest(
				customer.session_id, sha256(csrf_token.encode("utf-8")).hexdigest()
			)
	elif not csrf_token:
		csrf_token = secrets.token_urlsafe(32)
	_set_csrf_cookie(response, csrf_token, settings)
	if customer is None:
		return SessionStatusResponse(authenticated=False, csrf_token=csrf_token)
	return SessionStatusResponse(
		authenticated=True,
		customer_id=customer.customer_id,
		display_name=customer.display_name,
		email_verified=customer.email_verified,
		mobile_verified=customer.mobile_verified,
		transfer_eligible=customer.transfer_eligible,
		csrf_token=csrf_token,
	)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
	response: Response,
	customer: AuthenticatedCustomer = Depends(require_session_csrf),
	service: CustomerAuthService = Depends(get_auth_service),
	settings: Settings = Depends(get_settings),
) -> Response:
	if customer.session_id is not None:
		service.logout(customer.session_id)
	response.delete_cookie(key=settings.session_cookie_name, path="/")
	response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")
	response.status_code = status.HTTP_204_NO_CONTENT
	return response


@router.post(
	"/auth/contact-verification",
	response_model=ContactVerificationRequestResponse,
	status_code=status.HTTP_202_ACCEPTED,
)
def request_contact_verification(
	payload: ContactVerificationRequest,
	customer: AuthenticatedCustomer = Depends(require_session_csrf),
	service: CustomerAuthService = Depends(get_auth_service),
	settings: Settings = Depends(get_settings),
) -> ContactVerificationRequestResponse:
	service.request_contact_verification(customer.customer_id, payload.channel)
	if (
		settings.mock_contact_verification
		and payload.channel == ContactChannel.EMAIL
	):
		return ContactVerificationRequestResponse(
			message="Local mock email is ready. Enter verification code 1234.",
			code_length=4,
		)
	return ContactVerificationRequestResponse(
		message="If this contact can be verified, a code has been sent.",
		code_length=6,
	)


@router.post(
	"/auth/contact-verification/confirm",
	response_model=ContactVerificationResponse,
)
def confirm_contact_verification(
	payload: ContactVerificationConfirmRequest,
	customer: AuthenticatedCustomer = Depends(require_session_csrf),
	service: CustomerAuthService = Depends(get_auth_service),
) -> ContactVerificationResponse:
	result = service.confirm_contact_verification(
		customer.customer_id, payload.channel, payload.code
	)
	return ContactVerificationResponse(transfer_eligible=result.transfer_eligible)


@router.post(
	"/auth/password-reset/request", status_code=status.HTTP_202_ACCEPTED
)
def request_password_reset(
	payload: PasswordResetRequest,
	service: CustomerAuthService = Depends(get_auth_service),
	_origin_ok: None = Depends(require_same_origin),
):
	try:
		service.request_password_reset(payload.username, payload.channel)
	except InvalidOrExpiredChallenge:
		pass
	return {"message": "If the account is eligible, a reset code has been sent."}


@router.post(
	"/auth/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT
)
def confirm_password_reset(
	payload: PasswordResetConfirmRequest,
	service: CustomerAuthService = Depends(get_auth_service),
	_origin_ok: None = Depends(require_same_origin),
) -> Response:
	service.confirm_password_reset(payload.reset_code, payload.new_password)
	return Response(status_code=status.HTTP_204_NO_CONTENT)