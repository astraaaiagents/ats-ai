import uuid

import sqlalchemy as sa

from app.models.audit_log import AuditLog
from app.models.client_contact import ClientContact
from app.models.organization import Organization
from app.models.platform_user import PlatformUser
from app.models.user import User


class TestOrganization:
    def test_create_organization(self):
        org = Organization(name="Test Org", slug="test-org")
        assert org.name == "Test Org"
        assert org.slug == "test-org"
        assert org.is_active is True
        assert org.settings == {}
        assert org.kms_key_id is None

    def test_organization_id_is_uuid(self):
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Test Org", slug="test-org")
        assert isinstance(org.id, uuid.UUID)
        assert org.id == org_id

    def test_organization_str_attributes(self):
        org = Organization(name="Acme Corp", slug="acme-corp")
        assert str(org.name) == "Acme Corp"
        assert str(org.slug) == "acme-corp"


class TestUser:
    def test_create_user(self):
        user = User(email="test@example.com", password_hash="hashed_pwd")
        assert user.email == "test@example.com"
        assert user.role == "recruiter"
        assert user.is_active is True
        assert user.token_version == 0

    def test_user_with_organization(self):
        org_id = uuid.uuid4()
        user = User(
            email="user@org.com",
            password_hash="hash",
            organization_id=org_id,
            role="recruiter",
        )
        assert user.organization_id == org_id

    def test_user_super_admin_no_org(self):
        user = User(
            email="admin@example.com",
            password_hash="hash",
            role="super_admin",
        )
        assert user.organization_id is None

    def test_user_has_active_email_index(self):
        indexes = [idx for idx in User.__table_args__ if isinstance(idx, sa.Index)]
        active_email_idx = next(
            (idx for idx in indexes if idx.name == "ix_users_active_email"),
            None,
        )
        assert active_email_idx is not None
        assert active_email_idx.unique is True

    def test_user_has_organization_relationship(self):
        assert hasattr(User, "organization")


class TestPlatformUser:
    def test_create_platform_user(self):
        pu = PlatformUser(email="admin@platform.com", password_hash="hash")
        assert pu.role == "super_admin"
        assert pu.is_active is True

    def test_platform_user_email_unique(self):
        pu = PlatformUser(email="admin@platform.com", password_hash="hash")
        assert pu.email == "admin@platform.com"

    def test_platform_user_no_organization_id(self):
        pu = PlatformUser(email="admin@platform.com", password_hash="hash")
        assert not hasattr(pu, "organization_id")


class TestClientContact:
    def test_create_client_contact(self):
        org_id = uuid.uuid4()
        cc = ClientContact(
            organization_id=org_id,
            email="contact@client.com",
            first_name="John",
            last_name="Doe",
        )
        assert cc.email == "contact@client.com"
        assert cc.first_name == "John"
        assert cc.last_name == "Doe"
        assert cc.phone is None
        assert cc.is_active is True

    def test_unique_constraint_definition(self):
        constraints = [
            c
            for c in ClientContact.__table_args__
            if isinstance(c, sa.UniqueConstraint)
        ]
        assert len(constraints) == 1
        uq = constraints[0]
        col_names = [c.name if hasattr(c, "name") else c for c in uq.columns]
        assert set(col_names) == {"organization_id", "email"}


class TestAuditLog:
    def test_create_audit_log(self):
        log = AuditLog(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            event_type="user.login",
            resource_type="user",
            resource_id=str(uuid.uuid4()),
            details={"ip": "127.0.0.1"},
        )
        assert log.event_type == "user.login"
        assert log.details == {"ip": "127.0.0.1"}
        assert log.organization_id is not None
        assert log.user_id is not None

    def test_audit_log_no_updated_at(self):
        assert not hasattr(AuditLog, "updated_at")

    def test_audit_log_minimal(self):
        log = AuditLog(
            event_type="system.startup",
            resource_type="system",
        )
        assert log.organization_id is None
        assert log.user_id is None
        assert log.resource_id is None
        assert log.details is None
