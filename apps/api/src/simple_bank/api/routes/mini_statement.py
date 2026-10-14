"""Mini statement API routes."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from simple_bank.api.schemas.mini_statement_schema import MiniStatementResponse
from simple_bank.domain.errors import NotFound
from simple_bank.security.context import AuthenticatedCustomer, get_authenticated_customer
from simple_bank.services.mini_statement_service import MiniStatementService


router = APIRouter()


def get_mini_statement_service(request: Request) -> MiniStatementService:
    """Get mini statement service from application state."""
    service: MiniStatementService | None = getattr(
        request.app.state, "mini_statement_service", None
    )
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mini statement service is not configured.",
        )
    return service


@router.get(
    "/accounts/{account_number}/mini-statement",
    response_model=MiniStatementResponse,
    status_code=200
)
def get_mini_statement(
    account_number: str,
    customer: AuthenticatedCustomer = Depends(get_authenticated_customer),
    service: MiniStatementService = Depends(get_mini_statement_service),
) -> MiniStatementResponse:
    """Get mini statement for an account.
    
    Returns the last 10 transactions for an account, with current balance.
    Account number in response is masked (XXXX + last 4 digits).
    
    Returns 404 if account is not found or user is not authorized to access it
    (intentional: prevents account enumeration attacks).
    
    Args:
        account_number: The account number to retrieve statement for.
        customer: Authenticated customer making the request.
        service: Mini statement service.
        
    Returns:
        MiniStatementResponse with account info and last 10 transactions.
        
    Raises:
        HTTPException 404: If account not found or unauthorized.
        HTTPException 503: If service not configured.
    """
    try:
        return service.get_mini_statement(account_number, customer.customer_id)
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found.",
        )
