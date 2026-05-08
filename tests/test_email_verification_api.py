from datetime import datetime, timedelta

from backend.app.core.config import settings
from backend.app.models.account import EmailVerification


def test_email_verification_send_success(client, monkeypatch):
    monkeypatch.setattr(settings, "email_dev_mode", True)
    monkeypatch.setattr(settings, "email_verification_resend_cooldown_seconds", 60)
    monkeypatch.setattr(settings, "email_verification_expire_minutes", 5)

    response = client.post(
        "/api/v1/auth/email/send",
        json={"email": "newuser@example.com", "purpose": "SIGNUP"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "verification email sent"
    assert body["data"]["email"] == "newuser@example.com"
    assert body["data"]["purpose"] == "SIGNUP"
    assert body["data"]["dev_code"]


def test_email_verification_send_invalid_email_fails(client):
    response = client.post(
        "/api/v1/auth/email/send",
        json={"email": "not-an-email", "purpose": "SIGNUP"},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["message"] == "invalid email format"


def test_email_verification_verify_invalid_code_fails(client, monkeypatch):
    monkeypatch.setattr(settings, "email_dev_mode", True)

    send_response = client.post(
        "/api/v1/auth/email/send",
        json={"email": "verify-invalid@example.com", "purpose": "SIGNUP"},
    )
    assert send_response.status_code == 200

    verify_response = client.post(
        "/api/v1/auth/email/verify",
        json={"email": "verify-invalid@example.com", "code": "999999", "purpose": "SIGNUP"},
    )
    assert verify_response.status_code == 400
    body = verify_response.json()
    assert body["message"] == "invalid verification code"


def test_email_verification_verify_success(client, monkeypatch):
    monkeypatch.setattr(settings, "email_dev_mode", True)

    send_response = client.post(
        "/api/v1/auth/email/send",
        json={"email": "verify-success@example.com", "purpose": "SIGNUP"},
    )
    code = send_response.json()["data"]["dev_code"]

    verify_response = client.post(
        "/api/v1/auth/email/verify",
        json={"email": "verify-success@example.com", "code": code, "purpose": "SIGNUP"},
    )
    assert verify_response.status_code == 200
    body = verify_response.json()
    assert body["message"] == "email verified"
    assert body["data"]["verified"] is True


def test_email_verification_status_reflects_verified_state(client, monkeypatch):
    monkeypatch.setattr(settings, "email_dev_mode", True)

    send_response = client.post(
        "/api/v1/auth/email/send",
        json={"email": "status-check@example.com", "purpose": "SIGNUP"},
    )
    code = send_response.json()["data"]["dev_code"]

    verify_response = client.post(
        "/api/v1/auth/email/verify",
        json={"email": "status-check@example.com", "code": code, "purpose": "SIGNUP"},
    )
    assert verify_response.status_code == 200

    status_response = client.get(
        "/api/v1/auth/email/status",
        params={"email": "status-check@example.com", "purpose": "SIGNUP"},
    )
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["data"]["email"] == "status-check@example.com"
    assert body["data"]["purpose"] == "SIGNUP"
    assert body["data"]["verified"] is True


def test_email_verification_reuse_fails(client, monkeypatch):
    monkeypatch.setattr(settings, "email_dev_mode", True)

    send_response = client.post(
        "/api/v1/auth/email/send",
        json={"email": "reuse@example.com", "purpose": "SIGNUP"},
    )
    code = send_response.json()["data"]["dev_code"]

    first_verify = client.post(
        "/api/v1/auth/email/verify",
        json={"email": "reuse@example.com", "code": code, "purpose": "SIGNUP"},
    )
    assert first_verify.status_code == 200

    second_verify = client.post(
        "/api/v1/auth/email/verify",
        json={"email": "reuse@example.com", "code": code, "purpose": "SIGNUP"},
    )
    assert second_verify.status_code == 400
    assert second_verify.json()["message"] == "verification code already used"


def test_email_verification_expired_code_fails(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "email_dev_mode", True)

    send_response = client.post(
        "/api/v1/auth/email/send",
        json={"email": "expired@example.com", "purpose": "SIGNUP"},
    )
    code = send_response.json()["data"]["dev_code"]

    verification = (
        db_session.query(EmailVerification)
        .filter(EmailVerification.email == "expired@example.com", EmailVerification.purpose == "SIGNUP")
        .order_by(EmailVerification.created_at.desc())
        .first()
    )
    verification.expires_at = datetime.utcnow() - timedelta(minutes=1)
    db_session.commit()

    verify_response = client.post(
        "/api/v1/auth/email/verify",
        json={"email": "expired@example.com", "code": code, "purpose": "SIGNUP"},
    )
    assert verify_response.status_code == 400
    assert verify_response.json()["message"] == "verification code expired"


def test_email_verification_attempts_exceeded(client, monkeypatch):
    monkeypatch.setattr(settings, "email_dev_mode", True)
    monkeypatch.setattr(settings, "email_verification_max_attempts", 5)

    send_response = client.post(
        "/api/v1/auth/email/send",
        json={"email": "attempts@example.com", "purpose": "SIGNUP"},
    )
    assert send_response.status_code == 200

    for _ in range(4):
        response = client.post(
            "/api/v1/auth/email/verify",
            json={"email": "attempts@example.com", "code": "000000", "purpose": "SIGNUP"},
        )
        assert response.status_code == 400

    final_response = client.post(
        "/api/v1/auth/email/verify",
        json={"email": "attempts@example.com", "code": "000000", "purpose": "SIGNUP"},
    )
    assert final_response.status_code == 429
    assert final_response.json()["message"] == "verification attempts exceeded"


def test_email_verification_resend_cooldown(client, monkeypatch):
    monkeypatch.setattr(settings, "email_dev_mode", True)
    monkeypatch.setattr(settings, "email_verification_resend_cooldown_seconds", 60)

    first_response = client.post(
        "/api/v1/auth/email/send",
        json={"email": "cooldown@example.com", "purpose": "SIGNUP"},
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/api/v1/auth/email/send",
        json={"email": "cooldown@example.com", "purpose": "SIGNUP"},
    )
    assert second_response.status_code == 429
    assert second_response.json()["message"] == "verification resend cooldown"


def test_signup_not_blocked_when_email_verification_not_required(client, monkeypatch):
    monkeypatch.setattr(settings, "email_verification_required", False)

    response = client.post(
        "/api/v1/auth/customers/signup",
        json={
            "email": "signup-open@example.com",
            "password": "demo1234!",
            "name": "Signup Open",
            "phone": "010-7777-8888",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["email"] == "signup-open@example.com"


def test_signup_blocked_when_email_verification_required(client, monkeypatch):
    monkeypatch.setattr(settings, "email_verification_required", True)

    response = client.post(
        "/api/v1/auth/customers/signup",
        json={
            "email": "signup-locked@example.com",
            "password": "demo1234!",
            "name": "Signup Locked",
            "phone": "010-1111-9999",
        },
    )
    assert response.status_code == 400
    assert response.json()["message"] == "email verification required"
