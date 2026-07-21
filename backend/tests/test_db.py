from unittest.mock import AsyncMock, MagicMock, patch

import pytest

ALEMBIC_INI = "backend/db/alembic.ini"


class TestAlembicConfig:
    def test_alembic_ini_exists(self):
        import os
        assert os.path.exists(ALEMBIC_INI)

    def test_alembic_config_loads(self):
        from alembic.config import Config
        config = Config(ALEMBIC_INI)
        assert config.get_main_option("script_location") == "backend/db"


class TestMigrationsImport:
    def test_script_directory_loads_all_revisions(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        config = Config(ALEMBIC_INI)
        script = ScriptDirectory.from_config(config)

        heads = script.get_heads()
        assert len(heads) == 1

        revisions = list(script.walk_revisions())
        assert len(revisions) == 2

        revisions_by_id = {r.revision: r for r in revisions}
        assert "001_initial_schema" in revisions_by_id
        assert "002_rls_policies" in revisions_by_id

    def test_initial_schema_attributes(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        config = Config(ALEMBIC_INI)
        script = ScriptDirectory.from_config(config)
        rev = script.get_revision("001_initial_schema")

        assert rev is not None
        assert rev.revision == "001_initial_schema"
        assert rev.down_revision is None

    def test_rls_policies_attributes(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        config = Config(ALEMBIC_INI)
        script = ScriptDirectory.from_config(config)
        rev = script.get_revision("002_rls_policies")

        assert rev is not None
        assert rev.revision == "002_rls_policies"
        assert rev.down_revision == "001_initial_schema"

    def test_migration_chain(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        config = Config(ALEMBIC_INI)
        script = ScriptDirectory.from_config(config)
        rev = script.get_revision("002_rls_policies")

        assert rev.down_revision == "001_initial_schema"


@pytest.mark.skip(reason="requires PostgreSQL")
class TestMigrationsRun:
    async def test_initial_migration_applies(self):
        pass

    async def test_rls_migration_applies(self):
        pass


class TestBootstrapScript:
    @pytest.mark.anyio
    async def test_creates_org_and_admin_when_empty(self):
        from backend.scripts.bootstrap import bootstrap

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.commit = AsyncMock()

        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__.return_value = mock_session

        with (
            patch("backend.scripts.bootstrap.create_async_engine", return_value=mock_engine),
            patch("backend.scripts.bootstrap.async_sessionmaker", return_value=session_factory),
            patch("backend.scripts.bootstrap.hash_password", return_value="hashed"),
        ):
            await bootstrap()

        assert mock_session.commit.called
        assert mock_engine.dispose.called

    @pytest.mark.anyio
    async def test_skips_when_org_exists(self):
        from backend.scripts.bootstrap import bootstrap

        org_result = MagicMock()
        org_result.scalar_one_or_none.return_value = "550e8400-e29b-41d4-a716-446655440000"

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=org_result)
        mock_session.commit = AsyncMock()

        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__.return_value = mock_session

        with (
            patch("backend.scripts.bootstrap.create_async_engine", return_value=mock_engine),
            patch("backend.scripts.bootstrap.async_sessionmaker", return_value=session_factory),
            patch("backend.scripts.bootstrap.hash_password", return_value="hashed"),
        ):
            await bootstrap()

        assert mock_session.commit.called
        assert mock_engine.dispose.called


class TestRlsScript:
    @pytest.mark.anyio
    async def test_enables_rls_on_all_tables(self):
        from backend.scripts.setup_rls import setup_rls

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        session_factory = MagicMock()
        session_factory.return_value.__aenter__.return_value = mock_session

        with (
            patch("backend.scripts.setup_rls.create_async_engine", return_value=mock_engine),
            patch("backend.scripts.setup_rls.async_sessionmaker", return_value=session_factory),
        ):
            await setup_rls()

        assert mock_session.execute.called
        assert mock_session.commit.called
        assert mock_engine.dispose.called


class TestScriptsDirectory:
    def test_bootstrap_has_main(self):
        from backend.scripts.bootstrap import main
        assert callable(main)

    def test_setup_rls_has_main(self):
        from backend.scripts.setup_rls import main
        assert callable(main)
