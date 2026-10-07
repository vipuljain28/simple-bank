from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from simple_bank.domain.errors import TransferError


async def transfer_error_response(request: Request, error: TransferError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"error_code": error.code, "message": error.message},
    )


async def request_validation_response(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    invalid_amount = any(
        "amount" in item.get("loc", ()) for item in error.errors()
    )
    if invalid_amount:
        body = {
            "error_code": "INVALID_AMOUNT",
            "message": "Enter a positive amount with exactly two decimal places.",
        }
    else:
        body = {"error_code": "INVALID_REQUEST", "message": "The request is malformed."}
    return JSONResponse(status_code=400, content=body)