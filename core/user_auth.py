import base64
import hashlib
import hmac
import logging
import os
import re
import secrets
from datetime import datetime, timezone

from core.database import connect_database, parameter_placeholder

logger = logging.getLogger(__name__)

PASSWORD_ITERATIONS = 600_000
PASSWORD_SALT_BYTES = 16
PASSWORD_HASH_BYTES = 32
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 1024
_DUMMY_SALT = b"XAIDA-login-timing-salt"
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthenticationStorageError(RuntimeError):
    pass


def normalize_email(email):
    return email.strip().casefold() if isinstance(email, str) else ""


def allowed_email_set():
    return {
        normalize_email(value)
        for value in os.getenv("XAIDA_ALLOWED_EMAILS", "").split(",")
        if normalize_email(value)
    }


def valid_email(email):
    normalized = normalize_email(email)
    return (
        len(normalized) <= 254
        and _EMAIL_PATTERN.fullmatch(normalized) is not None
    )


def password_error(password):
    if not isinstance(password, str):
        return "Enter a password."
    if len(password) < MIN_PASSWORD_LENGTH:
        return "Use a password with at least 12 characters."
    if len(password) > MAX_PASSWORD_LENGTH:
        return "Use a password with no more than 1024 characters."
    return None


def _password_digest(password, salt, iterations=PASSWORD_ITERATIONS):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=PASSWORD_HASH_BYTES,
    )


def _hash_password(password):
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    digest = _password_digest(password, salt)
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def _verify_password(password, encoded_hash):
    try:
        algorithm, raw_iterations, raw_salt, raw_digest = encoded_hash.split("$")
        iterations = int(raw_iterations)
        if algorithm != "pbkdf2_sha256" or not 1 <= iterations <= 2_000_000:
            return False
        salt = base64.b64decode(raw_salt, validate=True)
        expected_digest = base64.b64decode(raw_digest, validate=True)
        if len(salt) != PASSWORD_SALT_BYTES:
            return False
        return hmac.compare_digest(
            _password_digest(password, salt, iterations),
            expected_digest,
        )
    except (AttributeError, ValueError):
        return False


def _ensure_schema(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS xaida_users (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


def _database_call(operation):
    try:
        with connect_database() as connection:
            _ensure_schema(connection)
            return operation(connection, parameter_placeholder())
    except Exception as error:
        logger.error("XAIDA account storage operation failed.")
        raise AuthenticationStorageError(
            "XAIDA account storage is unavailable. Try again later or "
            "contact the application administrator."
        ) from error


def create_account(email, password):
    email = normalize_email(email)
    if not valid_email(email):
        raise ValueError("Enter a valid email address.")
    error = password_error(password)
    if error:
        raise ValueError(error)

    if email not in allowed_email_set():
        raise ValueError(
            "This email address is not approved for XAIDA. Contact your "
            "application administrator."
        )

    password_hash = _hash_password(password)

    def insert(connection, marker):
        cursor = connection.execute(
            "INSERT INTO xaida_users (email, password_hash, created_at) "
            f"VALUES ({marker}, {marker}, {marker}) "
            "ON CONFLICT (email) DO NOTHING",
            (email, password_hash, datetime.now(timezone.utc).isoformat()),
        )
        return cursor.rowcount == 1

    return _database_call(insert)


def authenticate_account(email, password):
    email = normalize_email(email)
    if (
        not valid_email(email)
        or not isinstance(password, str)
        or len(password) > MAX_PASSWORD_LENGTH
    ):
        _password_digest("", _DUMMY_SALT)
        return False

    if email not in allowed_email_set():
        _password_digest(password, _DUMMY_SALT)
        return False

    def find(connection, marker):
        return connection.execute(
            f"SELECT password_hash FROM xaida_users WHERE email = {marker}",
            (email,),
        ).fetchone()

    row = _database_call(find)
    if row is None:
        _password_digest(password, _DUMMY_SALT)
        return False
    return _verify_password(password, row[0])
