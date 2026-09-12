import pytest
from pydantic import ValidationError

from schemas.user import LoginRequest


def test_login_request_accepts_valid_credentials():
    req = LoginRequest(email="user@example.com", password="whatever")
    assert req.email == "user@example.com"
    assert req.password == "whatever"


def test_login_request_rejects_missing_email():
    with pytest.raises(ValidationError):
        LoginRequest(password="whatever")


def test_login_request_rejects_missing_password():
    with pytest.raises(ValidationError):
        LoginRequest(email="user@example.com")


def test_login_request_rejects_malformed_email():
    with pytest.raises(ValidationError):
        LoginRequest(email="not-an-email", password="whatever")


def test_login_request_rejects_empty_password():
    with pytest.raises(ValidationError):
        LoginRequest(email="user@example.com", password="")


def test_login_request_accepts_short_legacy_password():
    req = LoginRequest(email="user@example.com", password="abc")
    assert req.password == "abc"
