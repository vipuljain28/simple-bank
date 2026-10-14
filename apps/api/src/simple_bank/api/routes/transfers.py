from fastapi import APIRouter, Depends, HTTPException, Request, status

from simple_bank.api.schemas.transfers import TransferRequest, TransferResponse
from simple_bank.domain.account_numbers import mask_account_number
from simple_bank.domain.auth_errors import ContactVerificationRequired
from simple_bank.domain.transfers import TransferCommand
from simple_bank.api.security.csrf import require_session_csrf
from simple_bank.security.context import AuthenticatedCustomer
from simple_bank.services.transfer_service import TransferService


router = APIRouter()


def get_transfer_service(request: Request) -> TransferService:
    service: TransferService | None = getattr(request.app.state, "transfer_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transfer service is not configured.",
        )
    return service


@router.post("/transfers", response_model=TransferResponse, status_code=201)
def create_transfer(
    payload: TransferRequest,
    customer: AuthenticatedCustomer = Depends(require_session_csrf),
    service: TransferService = Depends(get_transfer_service),
) -> TransferResponse:
    if not customer.transfer_eligible:
        raise ContactVerificationRequired()
    result = service.execute(
        customer.customer_id,
        TransferCommand(
            request_id=payload.request_id,
            verification_proof=payload.verification_proof or "",
            from_account=payload.from_account,
            to_account=payload.to_account,
            amount=payload.amount,
        ),
    )
    return TransferResponse(
        transaction_id=result.transaction_id,
        request_id=result.request_id,
        from_account=mask_account_number(result.from_account),
        to_account=mask_account_number(result.to_account),
        amount=f"{result.amount:.2f}",
        status=result.status,
        created_at=result.created_at,
    )