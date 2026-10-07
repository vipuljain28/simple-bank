from typing import Protocol

from sqlalchemy.orm import Session


class UnitOfWork(Protocol):
    session: Session

    def commit(self) -> None: ...

    def rollback(self) -> None: ...