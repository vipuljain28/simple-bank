from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing import Annotated

from simple_bank.domain.auth import ContactChannel


class RegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    email: str
    mobile_number: str
    username: str
    password: str
    account_number_suffix: str


class RegistrationResponse(BaseModel):
    customer_id: str
    account_number: str
    account_type: str
    status: str
    transfer_eligible: bool


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str


class SessionStatusResponse(BaseModel):
    authenticated: bool
    csrf_token: str
    customer_id: str | None = None
    display_name: str | None = None
    email_verified: bool = False
    mobile_verified: bool = False
    transfer_eligible: bool = False


class LoginResponse(BaseModel):
    authenticated: bool = True
    customer_id: str
    csrf_token: str
    transfer_eligible: bool


class ContactVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: ContactChannel


class ContactVerificationRequestResponse(BaseModel):
    message: str
    code_length: int


class ContactVerificationConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: ContactChannel
    code: Annotated[str, StringConstraints(pattern=r"^(?:[0-9]{4}|[0-9]{6})$")]


class ContactVerificationResponse(BaseModel):
    transfer_eligible: bool


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    channel: ContactChannel


class PasswordResetConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reset_code: Annotated[str, StringConstraints(pattern=r"^[0-9]{6}$")]
    new_password: str = Field(min_length=12, max_length=128)