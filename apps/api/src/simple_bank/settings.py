from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    session_cookie_name: str = "simple_bank_session"
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"
    session_idle_timeout_seconds: int = 300
    session_max_age_seconds: int = 3600
    auth_code_pepper: str | None = None
    sqlite_create_schema: bool = False
    public_origin: str | None = None
    mock_contact_verification: bool = False

    def __post_init__(self) -> None:
        if self.session_cookie_samesite not in {"lax", "strict", "none"}:
            raise ValueError("SESSION_COOKIE_SAMESITE must be lax, strict, or none.")
        if self.session_cookie_samesite == "none" and not self.session_cookie_secure:
            raise ValueError("SameSite=None cookies require SESSION_COOKIE_SECURE=true.")
        if self.session_idle_timeout_seconds <= 0 or self.session_max_age_seconds <= 0:
            raise ValueError("Session lifetime settings must be positive integers.")
        if self.mock_contact_verification and not (
            self.database_url is not None
            and self.database_url.strip().lower().startswith("sqlite:")
            and self.sqlite_create_schema
        ):
            raise ValueError(
                "MOCK_CONTACT_VERIFICATION requires SQLite with SQLITE_CREATE_SCHEMA=true."
            )

    @classmethod
    def from_environment(cls) -> "Settings":
        same_site = os.environ.get("SESSION_COOKIE_SAMESITE", "lax").strip().lower()
        secure = os.environ.get("SESSION_COOKIE_SECURE", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return cls(
            database_url=os.environ.get("DATABASE_URL"),
            session_cookie_name=os.environ.get("SESSION_COOKIE_NAME", "simple_bank_session"),
            session_cookie_secure=secure,
            session_cookie_samesite=same_site,
            session_idle_timeout_seconds=int(
                os.environ.get("SESSION_IDLE_TIMEOUT_SECONDS", "300")
            ),
            session_max_age_seconds=int(os.environ.get("SESSION_MAX_AGE_SECONDS", "3600")),
            auth_code_pepper=os.environ.get("AUTH_CODE_PEPPER"),
            sqlite_create_schema=os.environ.get("SQLITE_CREATE_SCHEMA", "").strip().lower()
            in {"1", "true", "yes", "on"},
            public_origin=os.environ.get("PUBLIC_ORIGIN"),
            mock_contact_verification=os.environ.get(
                "MOCK_CONTACT_VERIFICATION", ""
            ).strip().lower()
            in {"1", "true", "yes", "on"},
        )