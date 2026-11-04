import sqlite3

import pytest

from core.user_auth import (
    authenticate_account,
    create_account,
    password_error,
    valid_email,
)


@pytest.fixture
def account_database(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "XAIDA_EVALUATION_DB_PATH",
        str(tmp_path / "xaida.sqlite3"),
    )
    monkeypatch.setenv(
        "XAIDA_ALLOWED_EMAILS",
        "auditor@example.org, Second@example.org",
    )
    return tmp_path / "xaida.sqlite3"


def test_approved_user_can_register_and_sign_in_case_insensitively(
    account_database,
):
    assert create_account("Auditor@Example.org", "correct horse battery") is True
    assert authenticate_account(
        "AUDITOR@example.org",
        "correct horse battery",
    )
    assert not authenticate_account(
        "auditor@example.org",
        "incorrect horse battery",
    )

    with sqlite3.connect(account_database) as connection:
        email, password_hash = connection.execute(
            "SELECT email, password_hash FROM xaida_users"
        ).fetchone()
    assert email == "auditor@example.org"
    assert password_hash.startswith("pbkdf2_sha256$")
    assert "correct horse battery" not in password_hash


def test_registration_requires_an_approved_email(account_database):
    with pytest.raises(ValueError, match="not approved"):
        create_account("uninvited@example.org", "correct horse battery")

    assert not authenticate_account(
        "uninvited@example.org",
        "correct horse battery",
    )


def test_duplicate_registration_is_reported(account_database):
    assert create_account("auditor@example.org", "correct horse battery")
    assert not create_account(
        "AUDITOR@example.org",
        "another correct horse battery",
    )


def test_account_rejects_short_passwords(account_database):
    assert password_error("short") == "Use a password with at least 12 characters."
    with pytest.raises(ValueError, match="at least 12 characters"):
        create_account("auditor@example.org", "short")


@pytest.mark.parametrize(
    "email",
    ["", "invalid", "person@example", "person @example.org"],
)
def test_email_validation_rejects_invalid_addresses(email):
    assert not valid_email(email)
