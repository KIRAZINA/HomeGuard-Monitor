import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import get_db, Base

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Create a test client with database dependency override."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_token(db_session: AsyncSession):
    """Create a test user and return auth token."""
    from app.services.auth_service import AuthService
    from app.schemas.user import UserCreate
    
    auth_service = AuthService(db_session)
    
    # Create test user
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword123",
        full_name="Test User"
    )
    user = await auth_service.create_user(user_data)
    
    # Generate token
    token = auth_service.create_access_token(
        data={"sub": user.email}
    )
    return token


@pytest_asyncio.fixture
async def auth_headers(test_user_token: str):
    """Return authorization headers for test requests."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest_asyncio.fixture
async def test_device(db_session: AsyncSession):
    """Create a test device."""
    from app.models.device import Device
    from app.schemas.device import DeviceType, DeviceStatus
    
    device = Device(
        name="Test Server",
        description="Test server for monitoring",
        device_type=DeviceType.SERVER,
        hostname="test-server",
        ip_address="192.168.1.100",
        location="Test Lab",
        status=DeviceStatus.ONLINE
    )
    
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)
    return device


@pytest_asyncio.fixture
async def test_metrics(db_session: AsyncSession, test_device):
    """Create test metrics for the test device."""
    from app.models.metric import Metric
    from datetime import datetime, timedelta
    
    metrics = []
    base_time = datetime.utcnow() - timedelta(hours=1)
    
    for i in range(10):
        metric = Metric(
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            value=50.0 + (i * 5),
            unit="percent",
            timestamp=base_time + timedelta(minutes=i * 6)
        )
        metrics.append(metric)
    
    db_session.add_all(metrics)
    await db_session.commit()
    return metrics
