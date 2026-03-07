# CareBridge Enterprise — Phase 1 MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build CareBridge Enterprise Phase 1 MVP — a healthcare SaaS platform for ICU serious illness communication with voice capture, AI-generated dual documentation, and physician workflow support.

**Architecture:** Feature-slice full-stack build across 4 slices: (1) Scaffold + Auth, (2) Voice + Transcription, (3) Output Generation + Review, (4) Finalization + Success. Backend is FastAPI + PostgreSQL + Redis. Frontend is React + TypeScript + Vite + Tailwind.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0 async, Alembic, python-jose, passlib[bcrypt], openai (Whisper), anthropic (Claude claude-sonnet-4-6), celery[redis], React 18, TypeScript, Vite, Tailwind CSS 3, React Router 6, Axios, Zustand.

**Working directory:** `C:\Users\msmsh\Downloads\expense\` (project root — backend/ and frontend/ are direct children)

---

## SLICE 1: Project Scaffold + Auth

---

### Task 1: Create project scaffold files

**Files:**
- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`

**Step 1: Create `.env.example`**

```bash
# .env.example
DATABASE_URL=postgresql+asyncpg://carebridge:carebridge@postgres:5432/carebridge
REDIS_URL=redis://redis:6379/0
SECRET_KEY=changeme-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=carebridge-audio
ENVIRONMENT=development
```

**Step 2: Create `docker-compose.yml`**

```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
      - VITE_WS_URL=ws://localhost:8000

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: carebridge
      POSTGRES_PASSWORD: carebridge
      POSTGRES_DB: carebridge
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U carebridge"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

  celery:
    build: ./backend
    volumes:
      - ./backend:/app
    env_file: .env
    depends_on:
      - redis
      - postgres
    command: celery -A app.tasks.celery_app worker --loglevel=info

volumes:
  postgres_data:
  minio_data:
```

**Step 3: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system -e ".[dev]"

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 4: Create `backend/pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "carebridge"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.9",
    "openai>=1.30.0",
    "anthropic>=0.28.0",
    "celery[redis]>=5.4.0",
    "boto3>=1.34.0",
    "pydantic-settings>=2.2.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "factory-boy>=3.3.0",
    "httpx>=0.27.0",
    "aiosqlite>=0.20.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Step 5: Create `backend/app/__init__.py`** (empty file)

**Step 6: Create `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://carebridge:carebridge@postgres:5432/carebridge"
    redis_url: str = "redis://redis:6379/0"
    secret_key: str = "changeme"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    openai_api_key: str = ""
    anthropic_api_key: str = ""

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "carebridge-audio"

    environment: str = "development"


settings = Settings()
```

**Step 7: Commit**

```bash
git add .env.example docker-compose.yml backend/
git commit -m "feat: scaffold project structure and Docker Compose"
```

---

### Task 2: FastAPI app factory + core modules

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/database.py`
- Create: `backend/app/core/security.py`
- Create: `backend/app/core/middleware.py`
- Create: `backend/app/core/exceptions.py`

**Step 1: Create `backend/app/core/database.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.environment == "development")
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Step 2: Create `backend/app/core/security.py`**

```python
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode["exp"] = expire
    to_encode["type"] = "refresh"
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
```

**Step 3: Create `backend/app/core/exceptions.py`**

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse


class CareBridgeException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


async def carebridge_exception_handler(request: Request, exc: CareBridgeException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
```

**Step 4: Create `backend/app/core/middleware.py`**

```python
import time
import uuid
import logging

from fastapi import Request

logger = logging.getLogger("carebridge")


async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"[{request_id}] {request.method} {request.url.path} → {response.status_code} ({duration:.3f}s)")
    return response
```

**Step 5: Create `backend/app/main.py`**

```python
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import CareBridgeException, carebridge_exception_handler
from app.core.middleware import request_logging_middleware

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="CareBridge Enterprise API",
    description="Serious illness communication and documentation platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BaseHTTPMiddleware, dispatch=request_logging_middleware)
app.add_exception_handler(CareBridgeException, carebridge_exception_handler)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "carebridge"}


# Routers imported after models are defined (added in later tasks)
```

**Step 6: Write the first test to verify the app starts**

Create `backend/tests/__init__.py` (empty) and `backend/tests/conftest.py`:

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.core.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

Create `backend/tests/test_health.py`:

```python
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

**Step 7: Run the test (from backend/ directory)**

```bash
cd backend
pip install -e ".[dev]" aiosqlite
pytest tests/test_health.py -v
```

Expected: PASS

**Step 8: Commit**

```bash
git add backend/app/core/ backend/app/main.py backend/tests/
git commit -m "feat: FastAPI app factory, core modules, and health check"
```

---

### Task 3: Database models + Alembic setup

**Files:**
- Create: `backend/app/auth/__init__.py`
- Create: `backend/app/auth/models.py`
- Create: `backend/app/conversations/__init__.py`
- Create: `backend/app/conversations/models.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

**Step 1: Create `backend/app/auth/models.py`**

```python
import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LicenseTier(str, enum.Enum):
    SINGLE = "SINGLE"
    MULTI_SYSTEM = "MULTI_SYSTEM"


class UserRole(str, enum.Enum):
    PHYSICIAN = "PHYSICIAN"
    NURSE = "NURSE"
    ADMIN = "ADMIN"
    RISK_OFFICER = "RISK_OFFICER"


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    license_tier: Mapped[LicenseTier] = mapped_column(Enum(LicenseTier), default=LicenseTier.SINGLE)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship("User", back_populates="hospital")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.PHYSICIAN)
    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    hospital: Mapped[Hospital] = relationship("Hospital", back_populates="users")
```

**Step 2: Create `backend/app/conversations/models.py`**

```python
import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ConversationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    FINALIZED = "FINALIZED"


class ToneSetting(str, enum.Enum):
    optimistic = "optimistic"
    neutral = "neutral"
    concerned = "concerned"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_alias: Mapped[str] = mapped_column(String(100), nullable=False)
    physician_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"))
    status: Mapped[ConversationStatus] = mapped_column(Enum(ConversationStatus), default=ConversationStatus.DRAFT)
    tone_setting: Mapped[ToneSetting] = mapped_column(Enum(ToneSetting), default=ToneSetting.neutral)
    risk_calibration: Mapped[float] = mapped_column(Float, default=0.5)
    participants: Mapped[list] = mapped_column(JSON, default=list)
    organ_supports: Mapped[list] = mapped_column(JSON, default=list)
    code_status_discussed: Mapped[bool] = mapped_column(Boolean, default=False)
    code_status_change: Mapped[str | None] = mapped_column(String(255), nullable=True)
    surrogate_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    surrogate_relationship: Mapped[str | None] = mapped_column(String(100), nullable=True)
    family_questions: Mapped[list] = mapped_column(JSON, default=list)
    clinician_annotations: Mapped[list] = mapped_column(JSON, default=list)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    segments: Mapped[list["ConversationSegment"]] = relationship("ConversationSegment", back_populates="conversation", order_by="ConversationSegment.segment_order")
    output: Mapped["GeneratedOutput | None"] = relationship("GeneratedOutput", back_populates="conversation", uselist=False)


class ConversationSegment(Base):
    __tablename__ = "conversation_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    segment_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="segments")


class RiskSeverity(str, enum.Enum):
    yellow = "yellow"
    red = "red"


class GeneratedOutput(Base):
    __tablename__ = "generated_outputs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), unique=True)
    physician_note: Mapped[dict] = mapped_column(JSON, nullable=False)
    family_summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="output")
```

**Step 3: Initialize Alembic**

```bash
cd backend
alembic init alembic
```

**Step 4: Update `backend/alembic/env.py`** — replace the existing content with:

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.config import settings
from app.core.database import Base

# Import models so they are registered
import app.auth.models  # noqa
import app.conversations.models  # noqa

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 5: Create initial migration**

```bash
cd backend
alembic revision --autogenerate -m "initial schema"
alembic upgrade head  # run only when postgres is running via docker-compose
```

**Step 6: Add model import to `backend/app/main.py`** (add after imports):

```python
# Import models to ensure they are registered with Base
import app.auth.models  # noqa
import app.conversations.models  # noqa
```

**Step 7: Update conftest.py** to import models before creating tables. Add after the imports:

```python
import app.auth.models  # noqa
import app.conversations.models  # noqa
```

**Step 8: Run tests to verify models register**

```bash
cd backend
pytest tests/test_health.py -v
```

Expected: PASS (models registered, SQLite test DB creates tables)

**Step 9: Commit**

```bash
git add backend/app/auth/ backend/app/conversations/models.py backend/alembic/
git commit -m "feat: database models for auth and conversations + Alembic setup"
```

---

### Task 4: Auth module — schemas, dependencies, router

**Files:**
- Create: `backend/app/auth/schemas.py`
- Create: `backend/app/auth/dependencies.py`
- Create: `backend/app/auth/router.py`
- Create: `backend/tests/test_auth.py`

**Step 1: Create `backend/app/auth/schemas.py`**

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.auth.models import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    hospital_id: uuid.UUID
    is_active: bool
    is_demo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    hospital_id: uuid.UUID
```

**Step 2: Create `backend/app/auth/dependencies.py`**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserRole
from app.core.database import get_db
from app.core.security import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_role(*roles: UserRole):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return checker
```

**Step 3: Create `backend/app/auth/router.py`**

```python
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import Hospital, LicenseTier, User, UserRole
from app.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from app.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

DEMO_HOSPITAL_NAME = "CareBridge Demo Hospital"


async def _get_or_create_demo_hospital(db: AsyncSession) -> Hospital:
    result = await db.execute(select(Hospital).where(Hospital.name == DEMO_HOSPITAL_NAME))
    hospital = result.scalar_one_or_none()
    if not hospital:
        hospital = Hospital(name=DEMO_HOSPITAL_NAME, license_tier=LicenseTier.SINGLE)
        db.add(hospital)
        await db.flush()
    return hospital


def _make_tokens(user_id: str, role: str, hospital_id: str, is_demo: bool = False) -> TokenResponse:
    payload = {"sub": user_id, "role": role, "hospital_id": hospital_id, "demo": is_demo}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")
    return _make_tokens(str(user.id), user.role, str(user.hospital_id))


@router.post("/demo", response_model=TokenResponse)
async def demo_login(db: AsyncSession = Depends(get_db)):
    hospital = await _get_or_create_demo_hospital(db)
    demo_email = f"demo-physician-{uuid.uuid4().hex[:8]}@carebridge.demo"
    demo_user = User(
        email=demo_email,
        hashed_password=hash_password("demo"),
        full_name="Dr. Demo Physician",
        role=UserRole.PHYSICIAN,
        hospital_id=hospital.id,
        is_demo=True,
    )
    db.add(demo_user)
    await db.flush()
    return _make_tokens(str(demo_user.id), demo_user.role, str(hospital.id), is_demo=True)


@router.post("/register", response_model=UserResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # In production, restrict to ADMIN only. For MVP, open for initial setup.
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        hospital_id=body.hospital_id,
    )
    db.add(user)
    await db.flush()
    return UserResponse.model_validate(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return _make_tokens(str(user.id), user.role, str(user.hospital_id), user.is_demo)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
```

**Step 4: Mount router in `backend/app/main.py`** — add after the exception handler line:

```python
from app.auth.router import router as auth_router
app.include_router(auth_router)
```

**Step 5: Write failing tests — create `backend/tests/test_auth.py`**

```python
import pytest
import uuid
from app.auth.models import Hospital, LicenseTier, User, UserRole
from app.core.security import hash_password


@pytest.fixture
async def hospital(db):
    h = Hospital(name="Test Hospital", license_tier=LicenseTier.SINGLE)
    db.add(h)
    await db.commit()
    await db.refresh(h)
    return h


@pytest.fixture
async def physician(db, hospital):
    u = User(
        email="dr.test@hospital.com",
        hashed_password=hash_password("password123"),
        full_name="Dr. Test Physician",
        role=UserRole.PHYSICIAN,
        hospital_id=hospital.id,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


async def test_login_success(client, physician):
    response = await client.post("/auth/login", json={"email": "dr.test@hospital.com", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client, physician):
    response = await client.post("/auth/login", json={"email": "dr.test@hospital.com", "password": "wrong"})
    assert response.status_code == 401


async def test_demo_login(client):
    response = await client.post("/auth/demo")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


async def test_me_endpoint(client, physician):
    login = await client.post("/auth/login", json={"email": "dr.test@hospital.com", "password": "password123"})
    token = login.json()["access_token"]
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "dr.test@hospital.com"


async def test_me_without_token(client):
    response = await client.get("/auth/me")
    assert response.status_code == 403  # HTTPBearer returns 403 when no credentials


async def test_refresh_token(client, physician):
    login = await client.post("/auth/login", json={"email": "dr.test@hospital.com", "password": "password123"})
    refresh_token = login.json()["refresh_token"]
    response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()
```

**Step 6: Run tests**

```bash
cd backend
pytest tests/test_auth.py -v
```

Expected: All PASS

**Step 7: Commit**

```bash
git add backend/app/auth/ backend/app/main.py backend/tests/test_auth.py
git commit -m "feat: auth module — login, demo mode, RBAC, JWT tokens"
```

---

### Task 5: React app scaffold + Login page

**Files:**
- Create: `frontend/` (Vite scaffold)
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/colors.ts`
- Create: `frontend/src/hooks/useAuth.ts`
- Create: `frontend/src/pages/Login.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/Dockerfile`

**Step 1: Scaffold the React app**

```bash
cd /c/Users/msmsh/Downloads/expense
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install axios react-router-dom zustand @types/react-router-dom
```

**Step 2: Configure `frontend/tailwind.config.js`**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: "#1E3A5F", light: "#2A4F82" },
        clinical: { DEFAULT: "#4A90D9", light: "#6BAAE4" },
        success: "#27AE60",
        warning: "#F39C12",
        danger: "#E74C3C",
        textPrimary: "#2C3E50",
        textSecondary: "#7F8C8D",
      },
    },
  },
  plugins: [],
};
```

**Step 3: Update `frontend/src/index.css`** — replace content:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-gray-50 text-textPrimary font-sans;
}
```

**Step 4: Create `frontend/src/lib/api.ts`**

```typescript
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refreshToken });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          error.config.headers.Authorization = `Bearer ${data.access_token}`;
          return api(error.config);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);
```

**Step 5: Create `frontend/src/hooks/useAuth.ts`**

```typescript
import { create } from "zustand";
import { api } from "../lib/api";

interface AuthState {
  user: { email: string; full_name: string; role: string; is_demo: boolean } | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  demoLogin: () => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true });
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const me = await api.get("/auth/me");
    set({ user: me.data, isLoading: false });
  },

  demoLogin: async () => {
    set({ isLoading: true });
    const { data } = await api.post("/auth/demo");
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const me = await api.get("/auth/me");
    set({ user: me.data, isLoading: false });
  },

  logout: () => {
    localStorage.clear();
    set({ user: null });
  },

  fetchMe: async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    const me = await api.get("/auth/me");
    set({ user: me.data });
  },
}));
```

**Step 6: Create `frontend/src/pages/Login.tsx`**

```tsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Login() {
  const { login, demoLogin, isLoading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate("/new-conversation");
    } catch {
      setError("Invalid email or password.");
    }
  };

  const handleDemo = async () => {
    setError("");
    try {
      await demoLogin();
      navigate("/new-conversation");
    } catch {
      setError("Demo login failed. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center px-4">
      <div className="bg-white rounded-2xl shadow-lg p-10 w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center mb-8">
          <div className="w-10 h-10 bg-navy rounded-lg flex items-center justify-center mr-3">
            <span className="text-white font-bold text-lg">CB</span>
          </div>
          <span className="text-2xl font-bold text-navy">CareBridge AI</span>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-clinical"
              placeholder="physician@hospital.com"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-clinical"
              placeholder="••••••••"
              required
            />
          </div>

          {error && <p className="text-danger text-sm">{error}</p>}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-navy text-white rounded-lg py-3 font-semibold hover:bg-navy-light transition-colors disabled:opacity-60"
          >
            {isLoading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        {/* Demo mode */}
        <div className="mt-6 text-center">
          <button
            onClick={handleDemo}
            disabled={isLoading}
            className="text-clinical font-semibold hover:underline text-sm"
          >
            Demo Mode (No PHI) →
          </button>
          <p className="text-textSecondary text-xs mt-1">Explore with synthetic patient data</p>
        </div>
      </div>

      {/* Footer */}
      <p className="mt-6 text-textSecondary text-xs text-center max-w-sm">
        This tool provides language assistance only and does not replace clinical judgment.
      </p>
    </div>
  );
}
```

**Step 7: Create `frontend/src/App.tsx`**

```tsx
import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import Login from "./pages/Login";

// Placeholder pages (implemented in later tasks)
const NewConversation = () => <div className="p-8 text-navy font-bold">New Conversation — Coming in Slice 2</div>;
const ConversationReview = () => <div className="p-8 text-navy font-bold">Review — Coming in Slice 3</div>;
const ConversationSuccess = () => <div className="p-8 text-navy font-bold">Success — Coming in Slice 4</div>;

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  return user ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  const { fetchMe } = useAuth();

  useEffect(() => {
    fetchMe();
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/new-conversation" element={<ProtectedRoute><NewConversation /></ProtectedRoute>} />
        <Route path="/conversations/:id/review" element={<ProtectedRoute><ConversationReview /></ProtectedRoute>} />
        <Route path="/conversations/:id/success" element={<ProtectedRoute><ConversationSuccess /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
```

**Step 8: Create `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**Step 9: Update `frontend/vite.config.ts`**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/auth": "http://backend:8000",
      "/conversations": "http://backend:8000",
      "/ws": { target: "ws://backend:8000", ws: true },
    },
  },
});
```

**Step 10: Verify frontend builds**

```bash
cd frontend
npm run build
```

Expected: Build succeeds with no errors.

**Step 11: Commit**

```bash
git add frontend/
git commit -m "feat: React app scaffold and Login page with demo mode"
```

---

## SLICE 2: Voice Capture + Transcription

---

### Task 6: Conversation CRUD endpoints + WebSocket transcription

**Files:**
- Create: `backend/app/conversations/schemas.py`
- Create: `backend/app/conversations/router.py`
- Create: `backend/app/conversations/voice.py`
- Create: `backend/tests/test_conversations.py`

**Step 1: Create `backend/app/conversations/schemas.py`**

```python
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.conversations.models import ConversationStatus, ToneSetting


class ConversationCreate(BaseModel):
    patient_alias: str
    tone_setting: ToneSetting = ToneSetting.neutral
    risk_calibration: float = 0.5
    participants: list[str] = []
    organ_supports: list[str] = []
    code_status_discussed: bool = False
    code_status_change: str | None = None
    surrogate_name: str | None = None
    surrogate_relationship: str | None = None
    family_questions: list[str] = []
    clinician_annotations: list[str] = []


class ConversationUpdate(BaseModel):
    tone_setting: ToneSetting | None = None
    risk_calibration: float | None = None
    participants: list[str] | None = None
    organ_supports: list[str] | None = None
    code_status_discussed: bool | None = None
    code_status_change: str | None = None
    surrogate_name: str | None = None
    surrogate_relationship: str | None = None
    family_questions: list[str] | None = None
    clinician_annotations: list[str] | None = None


class ConversationResponse(BaseModel):
    id: uuid.UUID
    patient_alias: str
    physician_id: uuid.UUID
    status: ConversationStatus
    tone_setting: ToneSetting
    risk_calibration: float
    participants: list[str]
    organ_supports: list[str]
    code_status_discussed: bool
    code_status_change: str | None
    surrogate_name: str | None
    surrogate_relationship: str | None
    family_questions: list[str]
    clinician_annotations: list[str]
    is_demo: bool
    created_at: datetime
    finalized_at: datetime | None
    full_transcript: str | None = None

    model_config = {"from_attributes": True}


class SegmentResponse(BaseModel):
    id: uuid.UUID
    text: str
    confidence: float
    segment_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GeneratedOutputResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    physician_note: dict
    family_summary: str
    risk_flags: list[dict]
    created_at: datetime

    model_config = {"from_attributes": True}
```

**Step 2: Create `backend/app/conversations/voice.py`**

```python
import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger("carebridge.voice")

MEDICAL_PROMPT = (
    "vasopressin, norepinephrine, epinephrine, dopamine, CRRT, continuous renal replacement therapy, "
    "BiPAP, CPAP, mechanical ventilation, intubation, extubation, tracheostomy, vasopressor, "
    "sepsis, septic shock, multi-organ failure, DNR, DNI, do not resuscitate, do not intubate, "
    "goals of care, prognosis, surrogate, healthcare proxy, advance directive, palliative care, "
    "comfort care, code status, family meeting, ICU, intensive care unit, ventilator, "
    "norepinephrine, phenylephrine, vasopressin, ECMO, dialysis, ARDS"
)

PROMPT_TRIGGER_KEYWORDS: dict[str, list[str]] = {
    "organ_support": ["ventilator", "vasopressor", "crrt", "bipap", "norepinephrine", "vasopressin", "dialysis", "ecmo"],
    "trajectory": ["prognosis", "trajectory", "weeks", "months", "decline", "improve", "recovery", "outlook"],
    "code_status": ["code status", "dnr", "dni", "resuscitate", "resuscitation", "full code"],
    "surrogate": [],  # always shown unless documented
}


@dataclass
class TranscriptionSegment:
    text: str
    confidence: float
    prompts: list[str]


def detect_prompt_triggers(text: str, surrogate_documented: bool = False) -> list[str]:
    text_lower = text.lower()
    triggered = []
    for key, keywords in PROMPT_TRIGGER_KEYWORDS.items():
        if key == "surrogate":
            if not surrogate_documented:
                triggered.append("surrogate")
        elif any(kw in text_lower for kw in keywords):
            triggered.append(key)
    return triggered


class TranscriptionService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def transcribe_bytes(self, audio_bytes: bytes, filename: str = "audio.webm") -> TranscriptionSegment:
        """Transcribe a chunk of audio bytes using Whisper."""
        import io
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        try:
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                prompt=MEDICAL_PROMPT,
                response_format="verbose_json",
            )
            text = response.text.strip()
            # Whisper verbose_json gives avg_logprob; approximate confidence
            confidence = 0.9  # default; can be computed from segments if needed
            prompts = detect_prompt_triggers(text)
            return TranscriptionSegment(text=text, confidence=confidence, prompts=prompts)
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return TranscriptionSegment(text="", confidence=0.0, prompts=[])
```

**Step 3: Create `backend/app/conversations/router.py`**

```python
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.conversations.models import Conversation, ConversationSegment, ConversationStatus
from app.conversations.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    GeneratedOutputResponse,
    SegmentResponse,
)
from app.conversations.voice import TranscriptionService
from app.core.database import get_db

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = Conversation(
        **body.model_dump(),
        physician_id=current_user.id,
        hospital_id=current_user.hospital_id,
        is_demo=current_user.is_demo,
    )
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return _to_response(conv)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = await _get_conversation_or_404(conversation_id, current_user, db)
    return _to_response(conv)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: uuid.UUID,
    body: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = await _get_conversation_or_404(conversation_id, current_user, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(conv, field, value)
    await db.flush()
    await db.refresh(conv)
    return _to_response(conv)


@router.post("/{conversation_id}/finalize", response_model=ConversationResponse)
async def finalize_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = await _get_conversation_or_404(conversation_id, current_user, db)
    if conv.status == ConversationStatus.FINALIZED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already finalized")
    conv.status = ConversationStatus.FINALIZED
    conv.finalized_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(conv)
    return _to_response(conv)


async def _get_conversation_or_404(conversation_id: uuid.UUID, user: User, db: AsyncSession) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.physician_id == user.id)
        .options(selectinload(Conversation.segments))
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


def _to_response(conv: Conversation) -> ConversationResponse:
    full_transcript = " ".join(seg.text for seg in conv.segments) if conv.segments else None
    return ConversationResponse(
        **{k: getattr(conv, k) for k in ConversationResponse.model_fields if k != "full_transcript"},
        full_transcript=full_transcript,
    )


# ─── WebSocket Transcription ───────────────────────────────────────────────────

@router.websocket("/ws/transcribe/{conversation_id}")
async def transcribe_ws(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    await websocket.accept()
    service = TranscriptionService()
    segment_order = 0

    # Verify conversation exists (simplified — no auth check on WS for MVP)
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        await websocket.close(code=4004)
        return

    try:
        audio_buffer = bytearray()
        while True:
            message = await websocket.receive()
            if "bytes" in message:
                audio_buffer.extend(message["bytes"])
                # Transcribe when buffer hits ~32KB (roughly 2s of audio)
                if len(audio_buffer) >= 32_000:
                    chunk = bytes(audio_buffer)
                    audio_buffer.clear()
                    segment = await service.transcribe_bytes(chunk)
                    if segment.text:
                        db_segment = ConversationSegment(
                            conversation_id=conversation_id,
                            text=segment.text,
                            confidence=segment.confidence,
                            segment_order=segment_order,
                        )
                        db.add(db_segment)
                        await db.commit()
                        segment_order += 1
                        await websocket.send_json({
                            "type": "transcription",
                            "text": segment.text,
                            "confidence": segment.confidence,
                            "prompts": segment.prompts,
                        })
            elif "text" in message and message["text"] == "DONE":
                # Flush remaining buffer
                if audio_buffer:
                    chunk = bytes(audio_buffer)
                    segment = await service.transcribe_bytes(chunk)
                    if segment.text:
                        db_segment = ConversationSegment(
                            conversation_id=conversation_id,
                            text=segment.text,
                            confidence=segment.confidence,
                            segment_order=segment_order,
                        )
                        db.add(db_segment)
                        await db.commit()
                        await websocket.send_json({
                            "type": "transcription",
                            "text": segment.text,
                            "confidence": segment.confidence,
                            "prompts": segment.prompts,
                        })
                await websocket.send_json({"type": "done"})
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
```

**Step 4: Mount conversation router in `backend/app/main.py`** — add:

```python
from app.conversations.router import router as conversation_router
app.include_router(conversation_router)
```

**Step 5: Write tests for conversation CRUD**

Create `backend/tests/test_conversations.py`:

```python
import pytest
from app.auth.models import Hospital, LicenseTier, User, UserRole
from app.core.security import hash_password


@pytest.fixture
async def hospital(db):
    h = Hospital(name="Test Hospital", license_tier=LicenseTier.SINGLE)
    db.add(h)
    await db.commit()
    await db.refresh(h)
    return h


@pytest.fixture
async def auth_headers(client, db, hospital):
    u = User(
        email="dr@test.com",
        hashed_password=hash_password("pw"),
        full_name="Dr. Test",
        role=UserRole.PHYSICIAN,
        hospital_id=hospital.id,
    )
    db.add(u)
    await db.commit()
    login = await client.post("/auth/login", json={"email": "dr@test.com", "password": "pw"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_create_conversation(client, auth_headers):
    response = await client.post(
        "/conversations/",
        json={"patient_alias": "Patient A", "tone_setting": "neutral"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["patient_alias"] == "Patient A"
    assert data["status"] == "DRAFT"


async def test_get_conversation(client, auth_headers):
    create = await client.post("/conversations/", json={"patient_alias": "Patient B"}, headers=auth_headers)
    conv_id = create.json()["id"]
    response = await client.get(f"/conversations/{conv_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == conv_id


async def test_update_conversation(client, auth_headers):
    create = await client.post("/conversations/", json={"patient_alias": "Patient C"}, headers=auth_headers)
    conv_id = create.json()["id"]
    response = await client.patch(
        f"/conversations/{conv_id}",
        json={"tone_setting": "concerned", "surrogate_name": "Jane Doe"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["tone_setting"] == "concerned"
    assert response.json()["surrogate_name"] == "Jane Doe"


async def test_finalize_conversation(client, auth_headers):
    create = await client.post("/conversations/", json={"patient_alias": "Patient D"}, headers=auth_headers)
    conv_id = create.json()["id"]
    response = await client.post(f"/conversations/{conv_id}/finalize", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "FINALIZED"
    assert response.json()["finalized_at"] is not None
```

**Step 6: Run tests**

```bash
cd backend
pytest tests/test_conversations.py -v
```

Expected: All PASS

**Step 7: Commit**

```bash
git add backend/app/conversations/ backend/app/main.py backend/tests/test_conversations.py
git commit -m "feat: conversation CRUD endpoints and WebSocket transcription pipeline"
```

---

### Task 7: Frontend — VoiceRecorder + NewConversation page

**Files:**
- Create: `frontend/src/components/VoiceRecorder.tsx`
- Create: `frontend/src/components/ToneSelector.tsx`
- Create: `frontend/src/components/PromptChips.tsx`
- Create: `frontend/src/hooks/useVoiceCapture.ts`
- Create: `frontend/src/hooks/useConversation.ts`
- Create: `frontend/src/pages/NewConversation.tsx`

**Step 1: Create `frontend/src/hooks/useConversation.ts`**

```typescript
import { create } from "zustand";
import { api } from "../lib/api";

interface Conversation {
  id: string;
  patient_alias: string;
  tone_setting: "optimistic" | "neutral" | "concerned";
  risk_calibration: number;
  participants: string[];
  organ_supports: string[];
  code_status_discussed: boolean;
  code_status_change: string | null;
  surrogate_name: string | null;
  surrogate_relationship: string | null;
  family_questions: string[];
  clinician_annotations: string[];
  status: string;
  full_transcript: string | null;
}

interface ConversationState {
  current: Conversation | null;
  create: (patientAlias: string) => Promise<Conversation>;
  update: (id: string, data: Partial<Conversation>) => Promise<void>;
  generate: (id: string) => Promise<any>;
  finalize: (id: string) => Promise<void>;
}

export const useConversation = create<ConversationState>((set) => ({
  current: null,

  create: async (patientAlias) => {
    const { data } = await api.post("/conversations/", { patient_alias: patientAlias });
    set({ current: data });
    return data;
  },

  update: async (id, updates) => {
    const { data } = await api.patch(`/conversations/${id}`, updates);
    set({ current: data });
  },

  generate: async (id) => {
    const { data } = await api.post(`/conversations/${id}/generate`);
    return data;
  },

  finalize: async (id) => {
    const { data } = await api.post(`/conversations/${id}/finalize`);
    set({ current: data });
  },
}));
```

**Step 2: Create `frontend/src/hooks/useVoiceCapture.ts`**

```typescript
import { useCallback, useRef, useState } from "react";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

interface TranscriptionMessage {
  type: "transcription" | "done" | "error";
  text?: string;
  confidence?: number;
  prompts?: string[];
}

interface UseVoiceCaptureOptions {
  conversationId: string;
  onTranscription: (text: string, prompts: string[]) => void;
  onDone: () => void;
}

export function useVoiceCapture({ conversationId, onTranscription, onDone }: UseVoiceCaptureOptions) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const audioQueueRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ws = new WebSocket(`${WS_URL}/conversations/ws/transcribe/${conversationId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0 && ws.readyState === WebSocket.OPEN) {
          ws.send(e.data);
        } else if (e.data.size > 0) {
          audioQueueRef.current.push(e.data); // offline queue
        }
      };

      mediaRecorder.start(250); // 250ms chunks
      setIsRecording(true);
    };

    ws.onmessage = (e) => {
      const msg: TranscriptionMessage = JSON.parse(e.data);
      if (msg.type === "transcription" && msg.text) {
        onTranscription(msg.text, msg.prompts || []);
      } else if (msg.type === "done") {
        onDone();
      }
    };

    ws.onerror = () => {
      console.error("WebSocket error — audio queued locally");
    };
  }, [conversationId, onTranscription, onDone]);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current?.stream.getTracks().forEach((t) => t.stop());
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send("DONE");
    }
    setIsRecording(false);
  }, []);

  return { isRecording, startRecording, stopRecording };
}
```

**Step 3: Create `frontend/src/components/ToneSelector.tsx`**

```tsx
type Tone = "optimistic" | "neutral" | "concerned";

interface ToneSelectorProps {
  value: Tone;
  onChange: (tone: Tone) => void;
}

const TONES: { value: Tone; label: string; emoji: string }[] = [
  { value: "optimistic", label: "Optimistic", emoji: "😊" },
  { value: "neutral", label: "Neutral", emoji: "😐" },
  { value: "concerned", label: "Concerned", emoji: "😟" },
];

export default function ToneSelector({ value, onChange }: ToneSelectorProps) {
  return (
    <div className="flex gap-2">
      {TONES.map((tone) => (
        <button
          key={tone.value}
          onClick={() => onChange(tone.value)}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium border-2 transition-all ${
            value === tone.value
              ? "border-clinical bg-clinical text-white"
              : "border-gray-200 bg-white text-textPrimary hover:border-clinical"
          }`}
        >
          <span>{tone.emoji}</span>
          <span>{tone.label}</span>
        </button>
      ))}
    </div>
  );
}
```

**Step 4: Create `frontend/src/components/PromptChips.tsx`**

```tsx
interface PromptChipsProps {
  prompts: string[];
  dismissed: Set<string>;
  onDismiss: (prompt: string) => void;
}

const PROMPT_LABELS: Record<string, string> = {
  organ_support: "Organ support discussed?",
  trajectory: "Trajectory communicated?",
  code_status: "Code status addressed?",
  surrogate: "Surrogate confirmed?",
};

export default function PromptChips({ prompts, dismissed, onDismiss }: PromptChipsProps) {
  const visible = prompts.filter((p) => !dismissed.has(p));
  if (visible.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {visible.map((prompt) => (
        <div
          key={prompt}
          className="flex items-center gap-2 bg-amber-50 border border-warning text-warning text-sm px-3 py-1.5 rounded-full"
        >
          <span>⚠️ {PROMPT_LABELS[prompt] || prompt}</span>
          <button
            onClick={() => onDismiss(prompt)}
            className="text-warning hover:text-amber-700 font-bold leading-none"
            aria-label="Dismiss"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
```

**Step 5: Create `frontend/src/components/VoiceRecorder.tsx`**

```tsx
interface VoiceRecorderProps {
  isRecording: boolean;
  onStart: () => void;
  onStop: () => void;
}

export default function VoiceRecorder({ isRecording, onStart, onStop }: VoiceRecorderProps) {
  return (
    <div className="flex flex-col items-center gap-4">
      <button
        onClick={isRecording ? onStop : onStart}
        className={`w-24 h-24 rounded-full flex items-center justify-center shadow-lg transition-all text-white text-4xl ${
          isRecording
            ? "bg-danger animate-pulse scale-110"
            : "bg-clinical hover:bg-clinical-light hover:scale-105"
        }`}
        aria-label={isRecording ? "Stop recording" : "Start recording"}
      >
        {isRecording ? "⏹" : "🎙️"}
      </button>
      <p className="text-sm text-textSecondary font-medium">
        {isRecording ? "Recording… tap to stop" : "Tap mic to add"}
      </p>
    </div>
  );
}
```

**Step 6: Create `frontend/src/pages/NewConversation.tsx`**

```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import PromptChips from "../components/PromptChips";
import ToneSelector from "../components/ToneSelector";
import VoiceRecorder from "../components/VoiceRecorder";
import { useConversation } from "../hooks/useConversation";
import { useVoiceCapture } from "../hooks/useVoiceCapture";

type Tone = "optimistic" | "neutral" | "concerned";

export default function NewConversation() {
  const navigate = useNavigate();
  const { create, update, generate } = useConversation();

  const [conversationId, setConversationId] = useState<string | null>(null);
  const [patientAlias, setPatientAlias] = useState("Patient A");
  const [tone, setTone] = useState<Tone>("neutral");
  const [transcript, setTranscript] = useState("");
  const [prompts, setPrompts] = useState<string[]>([]);
  const [dismissed, setDismissed] = useState(new Set<string>());
  const [annotations, setAnnotations] = useState<string[]>([]);
  const [annotationInput, setAnnotationInput] = useState("");
  const [familyQuestions, setFamilyQuestions] = useState<string[]>([]);
  const [questionInput, setQuestionInput] = useState("");
  const [surrogateDocumented, setSurrogateDocumented] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const ensureConversation = async () => {
    if (conversationId) return conversationId;
    const conv = await create(patientAlias);
    setConversationId(conv.id);
    return conv.id;
  };

  const { isRecording, startRecording, stopRecording } = useVoiceCapture({
    conversationId: conversationId || "pending",
    onTranscription: (text, newPrompts) => {
      setTranscript((prev) => prev + (prev ? " " : "") + text);
      setPrompts((prev) => [...new Set([...prev, ...newPrompts])]);
    },
    onDone: () => {},
  });

  const handleStartRecording = async () => {
    await ensureConversation();
    await startRecording();
  };

  const handleGenerate = async () => {
    const id = await ensureConversation();
    setIsGenerating(true);
    try {
      await update(id, {
        tone_setting: tone,
        clinician_annotations: annotations,
        family_questions: familyQuestions,
        surrogate_name: surrogateDocumented ? "Documented" : undefined,
      });
      await generate(id);
      navigate(`/conversations/${id}/review`);
    } catch (err) {
      console.error("Generation failed", err);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-navy text-white px-8 py-4 flex items-center justify-between">
        <span className="font-bold text-lg">CareBridge AI</span>
        <span className="text-sm opacity-70">ICU Communication Update</span>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* LEFT COLUMN */}
        <div className="space-y-6">
          {/* Patient alias */}
          <div>
            <label className="block text-sm font-medium text-textSecondary mb-1">Patient Alias</label>
            <input
              value={patientAlias}
              onChange={(e) => setPatientAlias(e.target.value)}
              className="border border-gray-200 rounded-lg px-4 py-2 w-full text-textPrimary"
            />
          </div>

          {/* Voice recorder */}
          <div className="bg-white rounded-2xl shadow-sm p-8 flex flex-col items-center">
            <VoiceRecorder isRecording={isRecording} onStart={handleStartRecording} onStop={stopRecording} />

            {/* Transcript display */}
            {transcript && (
              <div className="mt-6 w-full bg-gray-50 rounded-xl p-4 text-sm text-textPrimary leading-relaxed max-h-48 overflow-y-auto">
                {transcript}
              </div>
            )}

            <PromptChips
              prompts={prompts}
              dismissed={dismissed}
              onDismiss={(p) => setDismissed((prev) => new Set([...prev, p]))}
            />
          </div>

          {/* Tone selector */}
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <p className="text-sm font-semibold text-textPrimary mb-3">Tone Report</p>
            <ToneSelector value={tone} onChange={setTone} />
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="space-y-6">
          {/* Clinician annotations */}
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <p className="text-sm font-semibold text-textPrimary mb-3">Clinician Input</p>
            <div className="flex gap-2 mb-3">
              <input
                value={annotationInput}
                onChange={(e) => setAnnotationInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && annotationInput.trim()) {
                    setAnnotations((prev) => [...prev, annotationInput.trim()]);
                    setAnnotationInput("");
                  }
                }}
                placeholder="Add annotation... (Enter to save)"
                className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm"
              />
            </div>
            {annotations.map((a, i) => (
              <div key={i} className="text-sm text-textPrimary bg-gray-50 rounded-lg px-3 py-2 mb-1">
                • {a}
              </div>
            ))}
          </div>

          {/* Family questions */}
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <p className="text-sm font-semibold text-textPrimary mb-3">Family Questions</p>
            <input
              value={questionInput}
              onChange={(e) => setQuestionInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && questionInput.trim()) {
                  setFamilyQuestions((prev) => [...prev, questionInput.trim()]);
                  setQuestionInput("");
                }
              }}
              placeholder="Enter family question... (Enter to save)"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-2"
            />
            {familyQuestions.map((q, i) => (
              <div key={i} className="text-sm text-textSecondary bg-gray-50 rounded-lg px-3 py-2 mb-1 italic">
                "{q}"
              </div>
            ))}
          </div>

          {/* Surrogate toggle */}
          <div className="bg-white rounded-2xl shadow-sm p-6 flex items-center gap-3">
            <input
              type="checkbox"
              id="surrogate"
              checked={surrogateDocumented}
              onChange={(e) => setSurrogateDocumented(e.target.checked)}
              className="w-4 h-4 accent-clinical"
            />
            <label htmlFor="surrogate" className="text-sm text-textPrimary">Surrogate decision-maker confirmed</label>
          </div>

          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full bg-clinical text-white rounded-xl py-4 font-bold text-base hover:bg-clinical-light transition-colors disabled:opacity-60 shadow-md"
          >
            {isGenerating ? "Structuring your communication…" : "Generate Structured Communication →"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Step 7: Update `frontend/src/App.tsx`** — replace the NewConversation placeholder import:

```tsx
import NewConversation from "./pages/NewConversation";
```

**Step 8: Verify frontend compiles**

```bash
cd frontend
npm run build
```

Expected: Build succeeds.

**Step 9: Commit**

```bash
git add frontend/src/
git commit -m "feat: voice recorder, tone selector, prompt chips, NewConversation page"
```

---

## SLICE 3: Output Generation + Review

---

### Task 8: Claude output generator endpoint

**Files:**
- Create: `backend/app/conversations/generator.py`
- Modify: `backend/app/conversations/router.py` (add generate endpoint)
- Create: `backend/tests/test_generator.py`

**Step 1: Create `backend/app/conversations/generator.py`**

```python
import json
import logging

import anthropic

from app.config import settings
from app.conversations.models import Conversation, ConversationSegment

logger = logging.getLogger("carebridge.generator")

SYSTEM_PROMPT = """You are a medical documentation assistant specialized in serious illness communication in ICU settings. You generate two types of structured output:

1. PHYSICIAN NOTE INSERT: Medico-legally defensible, structured documentation suitable for EMR insertion. Uses precise clinical language. Documents what was COMMUNICATED, not what the clinical situation is. Must explicitly address uncertainty. Must document surrogate decision-maker.

2. FAMILY SUMMARY: Plain-language (6th grade reading level), emotionally calibrated summary for family members. Uses the NURSE mnemonic (Naming, Understanding, Respecting, Supporting, Exploring) for empathic framing. Never uses medical jargon without explanation. Never provides survival statistics or deterministic predictions.

CRITICAL RULES — NEVER VIOLATE:
- Never predict survival probability or use phrases like "X% chance of survival"
- Always acknowledge uncertainty explicitly in the physician note
- Always document who was present and their relationship to patient
- Physician note must document what was SAID, not what IS clinically
- Family summary must validate emotions before providing information
- Flag if input suggests multi-organ failure (≥3 organ supports), prolonged ventilation >14 days, or missing surrogate documentation

You must respond with ONLY valid JSON matching the exact schema provided. No preamble, no explanation."""

TONE_INSTRUCTIONS = {
    "optimistic": "Frame the trajectory with measured hope. Emphasize improvements while remaining factual. The family summary should be warm and forward-looking.",
    "neutral": "Present information factually without directional framing. The family summary should be clear and compassionate without minimizing or dramatizing.",
    "concerned": "Acknowledge the serious nature of the situation explicitly. Validate family distress as a normal response. The family summary should lead with emotional acknowledgment.",
}

OUTPUT_SCHEMA = {
    "physician_note": {
        "participants": "string — who was present and their role/relationship",
        "medical_status_explained": "string — structured summary of what was communicated about clinical status",
        "prognosis_discussed": "string — what trajectory/prognosis language was used; avoids deterministic predictions",
        "uncertainty_addressed": "string — how uncertainty was framed (medico-legally critical)",
        "family_understanding_noted": "string — assessment of family comprehension and emotional state",
        "code_status": "string — current code status, any changes made",
        "surrogate_decision_maker": "string — name, relationship, and confirmation of surrogate"
    },
    "family_summary": "string — approximately 150-200 words at 6th-grade reading level, emotionally calibrated",
    "risk_flags": [
        {
            "type": "string — e.g. missing_surrogate, multi_organ_failure, prolonged_ventilation, high_medico_legal_risk",
            "severity": "yellow or red",
            "message": "string — what was detected",
            "suggestion": "string — recommended action (not mandatory)"
        }
    ]
}


class OutputGenerator:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate(self, conversation: Conversation, segments: list[ConversationSegment]) -> dict:
        transcript = " ".join(seg.text for seg in segments) if segments else ""
        tone_instruction = TONE_INSTRUCTIONS[conversation.tone_setting]

        user_content = f"""Generate structured communication output for the following ICU family meeting.

TONE INSTRUCTION: {tone_instruction}

TRANSCRIPT:
{transcript or "(No voice transcript — using annotations only)"}

CLINICIAN ANNOTATIONS:
{chr(10).join(f"- {a}" for a in (conversation.clinician_annotations or [])) or "None provided"}

FAMILY QUESTIONS ASKED:
{chr(10).join(f"- {q}" for q in (conversation.family_questions or [])) or "None documented"}

PARTICIPANTS: {", ".join(conversation.participants) if conversation.participants else "Not documented"}
ORGAN SUPPORTS: {", ".join(conversation.organ_supports) if conversation.organ_supports else "None documented"}
CODE STATUS DISCUSSED: {"Yes" if conversation.code_status_discussed else "No"}
CODE STATUS CHANGE: {conversation.code_status_change or "None"}
SURROGATE DOCUMENTED: {"Yes — " + str(conversation.surrogate_name) + " (" + str(conversation.surrogate_relationship) + ")" if conversation.surrogate_name else "NOT DOCUMENTED"}
RISK CALIBRATION: {conversation.risk_calibration} (0=low risk, 1=high risk)

Respond with ONLY valid JSON matching this exact schema:
{json.dumps(OUTPUT_SCHEMA, indent=2)}"""

        message = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )

        raw = message.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        logger.info(f"Generated output for conversation {conversation.id}: {len(result.get('risk_flags', []))} risk flags")
        return result
```

**Step 2: Add generate endpoint to `backend/app/conversations/router.py`** — add these imports and endpoint:

Add import at top:
```python
from sqlalchemy.orm import selectinload
from app.conversations.generator import OutputGenerator
from app.conversations.models import GeneratedOutput
from app.conversations.schemas import GeneratedOutputResponse
```

Add endpoint after the finalize endpoint:
```python
@router.post("/{conversation_id}/generate", response_model=GeneratedOutputResponse)
async def generate_output(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.physician_id == current_user.id)
        .options(selectinload(Conversation.segments))
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    generator = OutputGenerator()
    output_data = await generator.generate(conv, conv.segments)

    # Upsert generated output
    existing = await db.execute(select(GeneratedOutput).where(GeneratedOutput.conversation_id == conversation_id))
    existing_output = existing.scalar_one_or_none()
    if existing_output:
        existing_output.physician_note = output_data["physician_note"]
        existing_output.family_summary = output_data["family_summary"]
        existing_output.risk_flags = output_data.get("risk_flags", [])
        output = existing_output
    else:
        output = GeneratedOutput(
            conversation_id=conversation_id,
            physician_note=output_data["physician_note"],
            family_summary=output_data["family_summary"],
            risk_flags=output_data.get("risk_flags", []),
        )
        db.add(output)

    await db.flush()
    await db.refresh(output)
    return GeneratedOutputResponse.model_validate(output)
```

**Step 3: Write generator tests — create `backend/tests/test_generator.py`**

```python
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_conversation():
    from app.conversations.models import Conversation, ToneSetting
    import uuid
    conv = MagicMock(spec=Conversation)
    conv.id = uuid.uuid4()
    conv.tone_setting = ToneSetting.neutral
    conv.participants = ["Dr. Smith", "Jane Doe (daughter)"]
    conv.organ_supports = ["mechanical ventilator", "vasopressin"]
    conv.code_status_discussed = True
    conv.code_status_change = None
    conv.surrogate_name = "Jane Doe"
    conv.surrogate_relationship = "daughter"
    conv.family_questions = ["Is he going to be okay?"]
    conv.clinician_annotations = ["Improving oxygenation", "Family distressed"]
    conv.risk_calibration = 0.6
    return conv


@pytest.fixture
def mock_segments():
    from app.conversations.models import ConversationSegment
    seg = MagicMock(spec=ConversationSegment)
    seg.text = "We discussed the patient's current condition including the need for mechanical ventilation and vasopressor support."
    return [seg]


MOCK_CLAUDE_RESPONSE = {
    "physician_note": {
        "participants": "Dr. Smith (attending), Jane Doe (daughter, surrogate)",
        "medical_status_explained": "Discussed ongoing need for mechanical ventilation and vasopressor support.",
        "prognosis_discussed": "Trajectory communicated as uncertain with potential for improvement.",
        "uncertainty_addressed": "Explicitly acknowledged that outcomes remain uncertain.",
        "family_understanding_noted": "Family expressed distress; appeared to understand critical nature.",
        "code_status": "Full code status maintained; no changes discussed.",
        "surrogate_decision_maker": "Jane Doe, daughter, confirmed as healthcare proxy."
    },
    "family_summary": "Your loved one remains critically ill and is being supported by a breathing machine and blood pressure medication. We spoke today about their current condition and what we hope to see in the coming days. I know this is an incredibly difficult time, and it is completely understandable to feel worried and overwhelmed. We are closely monitoring all changes and will keep you informed.",
    "risk_flags": []
}


async def test_generator_produces_valid_output(mock_conversation, mock_segments):
    from app.conversations.generator import OutputGenerator

    with patch("anthropic.AsyncAnthropic") as mock_anthropic:
        mock_client = AsyncMock()
        mock_anthropic.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps(MOCK_CLAUDE_RESPONSE))]
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        gen = OutputGenerator()
        gen.client = mock_client
        result = await gen.generate(mock_conversation, mock_segments)

    assert "physician_note" in result
    assert "family_summary" in result
    assert "risk_flags" in result
    assert "participants" in result["physician_note"]
    assert "uncertainty_addressed" in result["physician_note"]


async def test_generator_missing_surrogate_flag(mock_conversation, mock_segments):
    from app.conversations.generator import OutputGenerator

    mock_conversation.surrogate_name = None
    response_with_flag = dict(MOCK_CLAUDE_RESPONSE)
    response_with_flag["risk_flags"] = [
        {"type": "missing_surrogate", "severity": "red", "message": "No surrogate documented.", "suggestion": "Document surrogate decision-maker."}
    ]

    with patch("anthropic.AsyncAnthropic"):
        gen = OutputGenerator()
        mock_client = AsyncMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps(response_with_flag))]
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        gen.client = mock_client
        result = await gen.generate(mock_conversation, mock_segments)

    assert any(f["type"] == "missing_surrogate" for f in result["risk_flags"])


async def test_trigger_detection():
    from app.conversations.voice import detect_prompt_triggers

    text = "The patient is on vasopressor support and we discussed prognosis"
    prompts = detect_prompt_triggers(text, surrogate_documented=False)
    assert "organ_support" in prompts
    assert "trajectory" in prompts
    assert "surrogate" in prompts


async def test_trigger_no_surrogate_prompt_when_documented():
    from app.conversations.voice import detect_prompt_triggers

    text = "The patient is stable"
    prompts = detect_prompt_triggers(text, surrogate_documented=True)
    assert "surrogate" not in prompts
```

**Step 4: Run generator tests**

```bash
cd backend
pytest tests/test_generator.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add backend/app/conversations/generator.py backend/app/conversations/router.py backend/tests/test_generator.py
git commit -m "feat: Claude output generator with physician note, family summary, and risk flags"
```

---

### Task 9: ConversationReview frontend page

**Files:**
- Create: `frontend/src/components/FamilySummaryCard.tsx`
- Create: `frontend/src/components/PhysicianNoteCard.tsx`
- Create: `frontend/src/components/RiskFlagBanner.tsx`
- Create: `frontend/src/pages/ConversationReview.tsx`

**Step 1: Create `frontend/src/components/RiskFlagBanner.tsx`**

```tsx
interface RiskFlag {
  type: string;
  severity: "yellow" | "red";
  message: string;
  suggestion: string;
}

export default function RiskFlagBanner({ flags }: { flags: RiskFlag[] }) {
  if (flags.length === 0) return null;
  return (
    <div className="space-y-2 mb-4">
      {flags.map((flag, i) => (
        <div
          key={i}
          className={`rounded-xl px-4 py-3 flex gap-3 items-start ${
            flag.severity === "red"
              ? "bg-red-50 border border-danger text-danger"
              : "bg-amber-50 border border-warning text-amber-800"
          }`}
        >
          <span className="text-lg leading-none mt-0.5">{flag.severity === "red" ? "🔴" : "⚠️"}</span>
          <div>
            <p className="font-semibold text-sm">{flag.message}</p>
            <p className="text-xs mt-0.5 opacity-80">{flag.suggestion}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
```

**Step 2: Create `frontend/src/components/FamilySummaryCard.tsx`**

```tsx
import RiskFlagBanner from "./RiskFlagBanner";

interface RiskFlag {
  type: string;
  severity: "yellow" | "red";
  message: string;
  suggestion: string;
}

interface FamilySummaryCardProps {
  summary: string;
  riskFlags: RiskFlag[];
}

export default function FamilySummaryCard({ summary, riskFlags }: FamilySummaryCardProps) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-6 flex flex-col h-full">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 bg-success rounded-lg flex items-center justify-center">
          <span className="text-white text-sm">👨‍👩‍👧</span>
        </div>
        <h2 className="font-bold text-textPrimary text-lg">Family Update</h2>
        <span className="ml-auto text-xs text-textSecondary bg-gray-100 px-2 py-1 rounded-full">Plain language</span>
      </div>

      <RiskFlagBanner flags={riskFlags} />

      <div className="bg-gray-50 rounded-xl p-4 flex-1">
        <p className="text-textPrimary text-sm leading-relaxed">{summary}</p>
      </div>
    </div>
  );
}
```

**Step 3: Create `frontend/src/components/PhysicianNoteCard.tsx`**

```tsx
import { useState } from "react";

interface PhysicianNote {
  participants: string;
  medical_status_explained: string;
  prognosis_discussed: string;
  uncertainty_addressed: string;
  family_understanding_noted: string;
  code_status: string;
  surrogate_decision_maker: string;
}

interface PhysicianNoteCardProps {
  note: PhysicianNote;
  onCopy: () => void;
}

const SECTIONS = [
  { key: "participants", label: "Participants" },
  { key: "medical_status_explained", label: "Medical Status Explained" },
  { key: "prognosis_discussed", label: "Prognosis Discussed" },
  { key: "uncertainty_addressed", label: "Uncertainty Addressed" },
  { key: "family_understanding_noted", label: "Family Understanding Noted" },
  { key: "code_status", label: "Code Status" },
  { key: "surrogate_decision_maker", label: "Surrogate Decision-Maker" },
] as const;

function Section({ label, value }: { label: string; value: string }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="border-b border-gray-100 last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between py-3 text-left"
      >
        <span className="text-xs font-bold uppercase tracking-wide text-textSecondary">{label}</span>
        <span className="text-textSecondary text-sm">{open ? "▲" : "▼"}</span>
      </button>
      {open && <p className="text-sm text-textPrimary pb-3 leading-relaxed">{value}</p>}
    </div>
  );
}

export default function PhysicianNoteCard({ note, onCopy }: PhysicianNoteCardProps) {
  const fullNoteText = `SERIOUS ILLNESS COMMUNICATION NOTE\n\n${SECTIONS.map(
    (s) => `${s.label.toUpperCase()}:\n${note[s.key]}`
  ).join("\n\n")}`;

  return (
    <div className="bg-white rounded-2xl shadow-sm p-6 flex flex-col h-full">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 bg-navy rounded-lg flex items-center justify-center">
          <span className="text-white text-sm">📋</span>
        </div>
        <h2 className="font-bold text-textPrimary text-lg">Physician Note Insert</h2>
        <span className="ml-auto text-xs text-textSecondary bg-gray-100 px-2 py-1 rounded-full">EMR-ready</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {SECTIONS.map((s) => (
          <Section key={s.key} label={s.label} value={note[s.key] || "Not documented"} />
        ))}
      </div>

      <button
        onClick={() => {
          navigator.clipboard.writeText(fullNoteText);
          onCopy();
        }}
        className="mt-4 w-full bg-navy text-white rounded-xl py-3 font-semibold hover:bg-navy-light transition-colors"
      >
        Copy to EHR →
      </button>
    </div>
  );
}
```

**Step 4: Create `frontend/src/pages/ConversationReview.tsx`**

```tsx
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import FamilySummaryCard from "../components/FamilySummaryCard";
import PhysicianNoteCard from "../components/PhysicianNoteCard";
import { api } from "../lib/api";

export default function ConversationReview() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [output, setOutput] = useState<any>(null);
  const [copied, setCopied] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    api.get(`/conversations/${id}`)
      .then(async (conv) => {
        // Fetch generated output — try to get it, or generate if missing
        try {
          const { data } = await api.post(`/conversations/${id}/generate`);
          setOutput(data);
        } catch {
          setError("Failed to load generated output.");
        }
      })
      .catch(() => setError("Conversation not found."));
  }, [id]);

  const handleFinalize = async () => {
    if (!id) return;
    setFinalizing(true);
    try {
      await api.post(`/conversations/${id}/finalize`);
      navigate(`/conversations/${id}/success`);
    } catch {
      setError("Finalization failed. Please try again.");
      setFinalizing(false);
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-danger font-medium">{error}</p>
      </div>
    );
  }

  if (!output) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center gap-4">
        <div className="w-12 h-12 border-4 border-clinical border-t-transparent rounded-full animate-spin" />
        <p className="text-textSecondary font-medium">Structuring your communication…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-navy text-white px-8 py-4 flex items-center justify-between">
        <span className="font-bold text-lg">CareBridge AI</span>
        <span className="text-sm opacity-70">Review Generated Communication</span>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Output cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8" style={{ minHeight: "60vh" }}>
          <FamilySummaryCard summary={output.family_summary} riskFlags={output.risk_flags} />
          <PhysicianNoteCard
            note={output.physician_note}
            onCopy={() => { setCopied(true); setTimeout(() => setCopied(false), 3000); }}
          />
        </div>

        {/* Copied toast */}
        {copied && (
          <div className="fixed bottom-6 right-6 bg-success text-white px-4 py-3 rounded-xl shadow-lg font-medium animate-fade-in">
            ✓ Copied to clipboard
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-4 justify-end">
          <button
            onClick={() => navigate("/new-conversation")}
            className="px-6 py-3 border-2 border-gray-200 rounded-xl font-semibold text-textPrimary hover:border-clinical transition-colors"
          >
            ← Edit Inputs
          </button>
          <button
            onClick={handleFinalize}
            disabled={finalizing}
            className="px-8 py-3 bg-success text-white rounded-xl font-bold hover:bg-green-600 transition-colors disabled:opacity-60"
          >
            {finalizing ? "Logging…" : "Finalize & Log →"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Step 5: Update `frontend/src/App.tsx`** — replace the ConversationReview placeholder:

```tsx
import ConversationReview from "./pages/ConversationReview";
```

**Step 6: Verify frontend builds**

```bash
cd frontend
npm run build
```

Expected: PASS

**Step 7: Commit**

```bash
git add frontend/src/
git commit -m "feat: ConversationReview page with family summary and physician note cards"
```

---

## SLICE 4: Finalization + Success

---

### Task 10: Success page + Celery tasks setup

**Files:**
- Create: `frontend/src/pages/ConversationSuccess.tsx`
- Create: `backend/app/tasks/__init__.py`
- Create: `backend/app/tasks/celery_app.py`
- Create: `backend/app/tasks/transcription.py`

**Step 1: Create `frontend/src/pages/ConversationSuccess.tsx`**

```tsx
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../lib/api";

export default function ConversationSuccess() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [conversation, setConversation] = useState<any>(null);

  useEffect(() => {
    if (!id) return;
    api.get(`/conversations/${id}`).then(({ data }) => setConversation(data));
  }, [id]);

  const formattedDate = conversation
    ? new Date(conversation.finalized_at || conversation.created_at).toLocaleDateString("en-US", {
        weekday: "long", year: "numeric", month: "long", day: "numeric",
      })
    : "";

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-navy text-white px-8 py-4">
        <span className="font-bold text-lg">CareBridge AI</span>
      </header>

      <div className="max-w-2xl mx-auto px-6 py-16 text-center">
        {/* Checkmark */}
        <div className="w-28 h-28 bg-success rounded-full flex items-center justify-center mx-auto mb-8 shadow-lg">
          <span className="text-white text-6xl">✓</span>
        </div>

        <h1 className="text-3xl font-bold text-navy mb-2">Update Logged Successfully</h1>
        <p className="text-textSecondary mb-8">The communication record has been saved and timestamped.</p>

        {/* Summary card */}
        {conversation && (
          <div className="bg-white rounded-2xl shadow-sm p-6 text-left space-y-3 mb-8">
            <div className="flex justify-between text-sm">
              <span className="text-textSecondary font-medium">Date</span>
              <span className="text-textPrimary">{formattedDate}</span>
            </div>
            <div className="flex justify-between text-sm border-t pt-3">
              <span className="text-textSecondary font-medium">Patient</span>
              <span className="text-textPrimary">{conversation.patient_alias}</span>
            </div>
            <div className="flex justify-between text-sm border-t pt-3">
              <span className="text-textSecondary font-medium">Status</span>
              <span className="text-success font-semibold">✓ Finalized</span>
            </div>
            {conversation.output?.risk_flags?.length > 0 && (
              <div className="border-t pt-3">
                <span className="text-textSecondary text-sm font-medium">Flags detected: </span>
                {conversation.output.risk_flags.map((f: any, i: number) => (
                  <span key={i} className={`text-xs font-semibold px-2 py-0.5 rounded-full mr-1 ${
                    f.severity === "red" ? "bg-red-100 text-danger" : "bg-amber-100 text-amber-700"
                  }`}>
                    {f.type.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => navigate("/new-conversation")}
            className="bg-clinical text-white px-8 py-3 rounded-xl font-bold hover:bg-clinical-light transition-colors"
          >
            Start New Update
          </button>
          <button
            disabled
            title="PDF export available in Phase 2"
            className="border-2 border-gray-200 text-textSecondary px-8 py-3 rounded-xl font-semibold opacity-50 cursor-not-allowed"
          >
            Export Log PDF → (Phase 2)
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Update `frontend/src/App.tsx`** — replace ConversationSuccess placeholder:

```tsx
import ConversationSuccess from "./pages/ConversationSuccess";
```

**Step 3: Create `backend/app/tasks/celery_app.py`**

```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "carebridge",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.transcription"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
```

**Step 4: Create `backend/app/tasks/transcription.py`**

```python
import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger("carebridge.tasks")


@celery_app.task(bind=True, max_retries=3)
def transcribe_audio_file(self, conversation_id: str, s3_key: str):
    """
    Fallback async transcription task.
    Called when WebSocket fails mid-session and client uploads full audio file.
    """
    try:
        asyncio.run(_transcribe_and_store(conversation_id, s3_key))
    except Exception as exc:
        logger.error(f"Transcription task failed for {conversation_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)


async def _transcribe_and_store(conversation_id: str, s3_key: str):
    # Import here to avoid circular imports
    import io
    import boto3
    from openai import AsyncOpenAI
    from sqlalchemy import select
    from app.config import settings
    from app.core.database import AsyncSessionLocal
    from app.conversations.models import Conversation, ConversationSegment
    from app.conversations.voice import TranscriptionService, MEDICAL_PROMPT

    # Download audio from MinIO/S3
    s3 = boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
    )
    obj = s3.get_object(Bucket=settings.minio_bucket, Key=s3_key)
    audio_bytes = obj["Body"].read()

    service = TranscriptionService()
    segment = await service.transcribe_bytes(audio_bytes, "audio.webm")

    async with AsyncSessionLocal() as db:
        from sqlalchemy import func
        result = await db.execute(
            select(func.count()).where(ConversationSegment.conversation_id == conversation_id)
        )
        existing_count = result.scalar()

        if segment.text:
            db_segment = ConversationSegment(
                conversation_id=conversation_id,
                text=segment.text,
                confidence=segment.confidence,
                segment_order=existing_count,
            )
            db.add(db_segment)
            await db.commit()
            logger.info(f"Stored fallback transcription segment for {conversation_id}")
```

**Step 5: Verify final frontend build**

```bash
cd frontend
npm run build
```

Expected: Build succeeds with all 4 pages.

**Step 6: Run all backend tests**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: All PASS

**Step 7: Final commit**

```bash
git add frontend/src/ backend/app/tasks/ backend/tests/
git commit -m "feat: success page, Celery task setup — Phase 1 MVP complete"
```

---

## Final Verification

### Start everything with Docker Compose

```bash
cd /c/Users/msmsh/Downloads/expense
cp .env.example .env
# Edit .env — set OPENAI_API_KEY and ANTHROPIC_API_KEY
docker-compose up --build
```

### Run Alembic migrations (first time)

```bash
docker-compose exec backend alembic upgrade head
```

### End-to-end test the physician workflow

1. Open `http://localhost:5173`
2. Click "Demo Mode (No PHI)" → lands on New Conversation
3. Enter patient alias, select Concerned tone
4. Click mic → speak a brief family meeting update (or type annotations)
5. Click "Generate Structured Communication"
6. Review physician note + family summary
7. Click "Copy to EHR" → clipboard verified
8. Click "Finalize & Log" → success screen with checkmark

### Run all backend tests

```bash
docker-compose exec backend pytest tests/ -v
```

Expected: All PASS
