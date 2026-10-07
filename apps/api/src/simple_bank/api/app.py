from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from simple_bank.api.error_mapping import request_validation_response, transfer_error_response
from simple_bank.api.logging import configure_logging
from simple_bank.api.routes.transfers import router as transfers_router
from simple_bank.domain.errors import TransferError
from simple_bank.security.context import CustomerContextProvider
from simple_bank.services.transfer_service import TransferService


def create_app(
    *,
    transfer_service: TransferService | None = None,
    customer_context_provider: CustomerContextProvider | None = None,
) -> FastAPI:
    configure_logging()
    application = FastAPI(title="Simple Bank API", version="1.0.0")
    application.state.transfer_service = transfer_service
    application.state.customer_context_provider = customer_context_provider
    application.include_router(transfers_router, prefix="/api/v1")
    application.add_exception_handler(TransferError, transfer_error_response)
    application.add_exception_handler(RequestValidationError, request_validation_response)
    return application


app = create_app()