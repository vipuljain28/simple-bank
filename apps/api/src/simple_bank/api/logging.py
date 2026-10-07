import logging
import re


_ACCOUNT_NUMBER = re.compile(r"(?<!\d)\d{4,}(?!\d)")


class AccountNumberRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _ACCOUNT_NUMBER.sub(
            lambda match: f"XXXX{match.group()[-4:]}", record.getMessage()
        )
        record.args = ()
        return True


def configure_logging() -> None:
    root = logging.getLogger()
    if not any(isinstance(item, AccountNumberRedactionFilter) for item in root.filters):
        root.addFilter(AccountNumberRedactionFilter())
    for handler in root.handlers:
        if not any(isinstance(item, AccountNumberRedactionFilter) for item in handler.filters):
            handler.addFilter(AccountNumberRedactionFilter())