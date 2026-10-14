from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from simple_bank.api.error_mapping import (
    auth_error_response,
    request_validation_response,
    transfer_error_response,
)
from simple_bank.api.logging import configure_logging
from simple_bank.api.routes.auth import router as auth_router
from simple_bank.api.routes.transfers import router as transfers_router
from simple_bank.api.routes.mini_statement import router as mini_statement_router
from simple_bank.domain.auth_errors import AuthError
from simple_bank.domain.errors import TransferError
from simple_bank.persistence.auth_repository import SqlAlchemyAuthRepository
from simple_bank.persistence.database import create_database_engine, create_session_factory
from simple_bank.persistence.models import Base
from simple_bank.persistence.transfer_repository import SqlAlchemyTransferRepository
from simple_bank.security.contact_delivery import ContactDelivery, UnconfiguredContactDelivery
from simple_bank.security.context import CustomerContextProvider, DatabaseCustomerContextProvider
from simple_bank.security.verification import RejectingTransferVerifier
from simple_bank.services.auth_service import CustomerAuthService
from simple_bank.services.transfer_service import TransferService
from simple_bank.settings import Settings


def create_app(
    *,
    transfer_service: TransferService | None = None,
    customer_context_provider: CustomerContextProvider | None = None,
    auth_service: CustomerAuthService | None = None,
    contact_delivery: ContactDelivery | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    configure_logging()
    application = FastAPI(title="Simple Bank API", version="1.0.0")
    resolved_settings = settings or Settings.from_environment()
    application.state.settings = resolved_settings
    application.add_api_route(
        "/health",
        lambda: {"status": "ok"},
        methods=["GET"],
        include_in_schema=False,
    )
    auth_repository = None
    if resolved_settings.database_url:
        engine = create_database_engine(resolved_settings.database_url)
        if resolved_settings.sqlite_create_schema:
            if engine.dialect.name != "sqlite":
                engine.dispose()
                raise ValueError("SQLITE_CREATE_SCHEMA can only be enabled with SQLite.")
            Base.metadata.create_all(engine)
        session_factory = create_session_factory(engine)
        auth_repository = SqlAlchemyAuthRepository(session_factory)
        application.state.database_engine = engine
        application.state.session_factory = session_factory
        application.router.add_event_handler("shutdown", engine.dispose)
        if auth_service is None:
            auth_service = CustomerAuthService(
                auth_repository,
                contact_delivery or UnconfiguredContactDelivery(),
                settings=resolved_settings,
            )
        if customer_context_provider is None:
            customer_context_provider = DatabaseCustomerContextProvider(
                auth_repository, resolved_settings
            )
        if transfer_service is None:
            transfer_service = TransferService(
                SqlAlchemyTransferRepository(session_factory),
                RejectingTransferVerifier(),
            )
    application.state.transfer_service = transfer_service
    application.state.customer_context_provider = customer_context_provider
    application.state.auth_service = auth_service
    application.state.contact_delivery = contact_delivery
    application.state.auth_repository = auth_repository
    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(transfers_router, prefix="/api/v1")
    application.include_router(mini_statement_router, prefix="/api/v1")
    application.add_exception_handler(TransferError, transfer_error_response)
    application.add_exception_handler(AuthError, auth_error_response)
    application.add_exception_handler(RequestValidationError, request_validation_response)
    return application


app = create_app()