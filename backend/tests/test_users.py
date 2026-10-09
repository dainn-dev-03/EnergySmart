from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.models import AuditLog
from tests.factories import auth_headers, create_user


def test_user_update_audit_records_before_and_after_values(
    client: TestClient, db_session: Session
) -> None:
    admin = create_user(db_session)
    target = create_user(db_session, username="target", role=UserRole.VIEWER)
    previous_email = target.email
    updated_email = "target-updated@energysmart.vn"

    response = client.put(
        f"/api/v1/users/{target.id}",
        headers=auth_headers(admin),
        json={"email": updated_email, "role": "MANAGER"},
    )

    assert response.status_code == 200
    log = db_session.scalar(select(AuditLog).where(AuditLog.action == "UPDATE_USER"))
    assert log is not None
    assert log.changes == {
        "email": [previous_email, updated_email],
        "role": ["VIEWER", "MANAGER"],
    }
    assert "password" not in log.changes
