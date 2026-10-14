from getpass import getpass
import os
from pathlib import Path
import subprocess
import sys

import psycopg
from psycopg import sql
from sqlalchemy.engine import URL


HOST = "127.0.0.1"
PORT = 5432
DATABASE = "simple_bank_test"
ADMIN_ROLE = "postgres"


def count_non_system_tables(connection: psycopg.Connection) -> int:
    return connection.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema NOT IN (%s, %s)",
        ("pg_catalog", "information_schema"),
    ).fetchone()[0]


def main() -> int:
    password = getpass(
        "Local PostgreSQL password for role postgres (input hidden): "
    )
    admin_connection = psycopg.connect(
        host=HOST,
        port=PORT,
        dbname="postgres",
        user=ADMIN_ROLE,
        password=password,
        connect_timeout=5,
        autocommit=True,
    )
    try:
        identity = admin_connection.execute(
            "SELECT current_database(), current_user, inet_server_addr()::text"
        ).fetchone()
        if identity != ("postgres", ADMIN_ROLE, HOST):
            raise SystemExit("Refusing: connection is not the expected localhost database.")

        database_exists = admin_connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (DATABASE,)
        ).fetchone()
        if not database_exists:
            admin_connection.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DATABASE))
            )
            print(f"Created localhost database {DATABASE}.")
        else:
            print(f"Found localhost database {DATABASE}; checking that it is empty.")
    finally:
        admin_connection.close()

    with psycopg.connect(
        host=HOST,
        port=PORT,
        dbname=DATABASE,
        user=ADMIN_ROLE,
        password=password,
        connect_timeout=5,
    ) as test_connection:
        if count_non_system_tables(test_connection):
            raise SystemExit(
                f"Refusing to run: {DATABASE} is not empty; no tables were changed."
            )

    database_url = URL.create(
        "postgresql+psycopg",
        username=ADMIN_ROLE,
        password=password,
        host=HOST,
        port=PORT,
        database=DATABASE,
    ).render_as_string(hide_password=False)
    child_environment = {
        key: os.environ[key]
        for key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP")
        if key in os.environ
    }
    child_environment["TEST_DATABASE_URL"] = database_url
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/integration", "-q"],
        cwd=Path(__file__).resolve().parent,
        env=child_environment,
        capture_output=True,
        text=True,
    )

    summary = next(
        (
            line.strip()
            for line in reversed(result.stdout.splitlines())
            if " passed" in line or " failed" in line or " error" in line
        ),
        "No pytest summary was produced.",
    )
    print(summary)
    if result.returncode:
        print("Integration tests failed; the final pytest output follows:")
        print("\n".join((result.stdout + result.stderr).splitlines()[-30:]))

    with psycopg.connect(
        host=HOST,
        port=PORT,
        dbname=DATABASE,
        user=ADMIN_ROLE,
        password=password,
        connect_timeout=5,
    ) as test_connection:
        remaining_tables = count_non_system_tables(test_connection)
    if remaining_tables:
        print(f"Warning: {remaining_tables} non-system tables remain in {DATABASE}.")
        return result.returncode or 1

    print(f"{DATABASE} is empty after the integration run.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())