from typing import Protocol

from simple_bank.domain.auth import ContactChannel


class ContactDelivery(Protocol):
    def send_code(self, channel: ContactChannel, destination: str, code: str) -> None: ...


class UnconfiguredContactDelivery:
    def send_code(self, channel: ContactChannel, destination: str, code: str) -> None:
        raise RuntimeError("No production email or SMS delivery provider is configured.")