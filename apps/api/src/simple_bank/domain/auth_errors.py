class AuthError(Exception):
    code = "AUTH_ERROR"
    status_code = 400
    message = "The request could not be completed."


class InvalidRegistration(AuthError):
    code = "INVALID_REGISTRATION"
    status_code = 400
    message = "Check the registration details and try again."


class RegistrationConflict(AuthError):
    code = "REGISTRATION_CONFLICT"
    status_code = 409
    message = "One or more registration details are unavailable."


class InvalidCredentials(AuthError):
    code = "INVALID_CREDENTIALS"
    status_code = 401
    message = "The sign-in details could not be verified."


class LoginTemporarilyThrottled(AuthError):
    code = "LOGIN_TEMPORARILY_THROTTLED"
    status_code = 429
    message = "Sign-in is temporarily unavailable. Try again later."


class ContactVerificationRequired(AuthError):
    code = "CONTACT_VERIFICATION_REQUIRED"
    status_code = 403
    message = "Verify your email or mobile number before transferring."


class InvalidOrExpiredChallenge(AuthError):
    code = "INVALID_OR_EXPIRED_CHALLENGE"
    status_code = 400
    message = "The verification code is invalid or expired."


class ContactDeliveryUnavailable(AuthError):
    code = "CONTACT_DELIVERY_UNAVAILABLE"
    status_code = 503
    message = "Verification delivery is temporarily unavailable."