import logging

from simple_bank.api.logging import configure_logging
from simple_bank.domain.account_numbers import mask_account_number


def test_account_number_display_is_masked():
    assert mask_account_number("000000001001") == "XXXX1001"


def test_child_logger_output_does_not_contain_full_account_number(caplog):
    configure_logging()
    account_number = "000000001001"
    caplog.set_level(logging.INFO)

    logging.getLogger("simple_bank.audit_test").info(
        "Transfer sender account %s", account_number
    )

    assert account_number not in caplog.text
    assert "XXXX1001" in caplog.text