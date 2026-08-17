import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    AsyncSessionTesting = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionTesting() as session:
        yield session
        await session.rollback()

@pytest.fixture
def override_db(db_session):
    async def _get_db_override():
        yield db_session
    return _get_db_override

@pytest.fixture(autouse=True)
def apply_db_override(app_instance, override_db):
    app_instance.dependency_overrides[get_db] = override_db
    yield
    app_instance.dependency_overrides.clear()

@pytest.fixture(scope="session")
def app_instance():
    return app
