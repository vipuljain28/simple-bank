from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str | None

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(database_url=os.environ.get("DATABASE_URL"))