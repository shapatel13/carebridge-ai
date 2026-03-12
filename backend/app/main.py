import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.auth.models import Hospital, User, UserRole
from app.auth.router import router as auth_router
from app.conversations.models import (
    Conversation,
    ConversationSegment,
    ConversationStatus,
    GeneratedOutput,
    ToneSetting,
)
from app.conversations.router import router as conversations_router
from app.core.database import Base, engine, AsyncSessionLocal
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_demo_data():
    """Seed the database with demo hospital, user, and sample conversation."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        # Check if demo data already exists
        result = await session.execute(select(User).where(User.email == "demo@carebridge.ai"))
        if result.scalar_one_or_none() is not None:
            logger.info("Demo data already exists, skipping seed")
            return

        # Create demo hospital
        hospital = Hospital(
            id="demo-hospital-001",
            name="Metro General Hospital",
            license_tier="SINGLE",
            settings={"branding": {"primary_color": "#1E3A5F"}},
        )
        session.add(hospital)

        # Create demo physician
        demo_user = User(
            id="demo-user-001",
            email="demo@carebridge.ai",
            hashed_password=hash_password("demo123"),
            full_name="Dr. Sarah Chen",
            role=UserRole.PHYSICIAN,
            hospital_id="demo-hospital-001",
            is_active=True,
            is_demo=True,
        )
        session.add(demo_user)

        # Create a sample finalized conversation for demo
        sample_conversation = Conversation(
            id="demo-conv-001",
            patient_alias="Patient A (Mr. Rodriguez)",
            physician_id="demo-user-001",
            hospital_id="demo-hospital-001",
            status=ConversationStatus.FINALIZED,
            tone_setting=ToneSetting.NEUTRAL,
            risk_calibration=0.5,
            participants=["Dr. Sarah Chen", "Maria Rodriguez (daughter)", "James Rodriguez (son)", "Nurse Patricia Williams"],
            organ_supports=["Mechanical ventilation", "Vasopressors (norepinephrine)"],
            code_status_discussed=True,
            code_status_change=None,
            surrogate_name="Maria Rodriguez",
            surrogate_relationship="Daughter (healthcare proxy)",
            family_questions=["Is he in pain?", "What would happen if we removed the ventilator?"],
            clinician_annotations=["Family appears to understand severity", "Surrogate beginning to consider goals of care"],
            is_demo=True,
        )
        session.add(sample_conversation)

        # Add transcript segments
        segments = [
            "Dr. Chen: Thank you all for coming today. I'm Dr. Chen, and I've been taking care of your father in the ICU. I wanted to give you an update on how he's doing and answer any questions you have.",
            "Maria: Thank you, doctor. We've been very worried.",
            "Dr. Chen: I understand, and it's completely natural to feel that way. Your father is currently on a breathing machine called a ventilator, which is helping him breathe. He's also receiving medication through his IV to help keep his blood pressure stable.",
            "Maria: Is he in pain?",
            "Dr. Chen: That's a really important question. We're giving him medication to keep him comfortable. The nurses check on his comfort level regularly, and right now he appears to be resting comfortably.",
            "Dr. Chen: I want to be honest with you about the overall picture. Over the past three days, despite our best efforts, your father's condition has been getting more serious rather than improving. His kidneys are showing signs of strain, and we may need to consider additional support for them.",
            "James: What does that mean exactly?",
            "Dr. Chen: It means we might need to use a machine to help clean his blood, similar to what dialysis does. I wish I could give you a definitive answer about what will happen, but the honest truth is that we don't know. What I can tell you is what we're seeing right now.",
            "Maria: Dad told me once that he wouldn't want to be kept alive by machines if there was no hope. I've been thinking about that a lot.",
            "Dr. Chen: Thank you for sharing that with us, Maria. That's very important information. I want you to know there's absolutely no rush to make any decisions right now. We can continue to provide full support while you and your family take the time you need to talk about what your father would want.",
        ]
        for i, text in enumerate(segments):
            session.add(ConversationSegment(
                conversation_id="demo-conv-001",
                text=text,
                confidence=0.95,
                segment_order=i,
            ))

        # Add generated output
        from app.conversations.generator import DEMO_OUTPUT
        session.add(GeneratedOutput(
            id="demo-output-001",
            conversation_id="demo-conv-001",
            physician_note=DEMO_OUTPUT["physician_note"],
            family_summary=DEMO_OUTPUT["family_summary"],
            risk_flags=DEMO_OUTPUT["risk_flags"],
        ))

        await session.commit()
        logger.info("Demo data seeded successfully")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Seed demo data
    await seed_demo_data()

    yield


app = FastAPI(
    title="CareBridge AI",
    description="ICU Serious Illness Communication Platform - AI-powered physician notes, family summaries, and risk detection",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")



# Static files and SPA serving
# Get the project root (two levels up from backend/app)
PROJECT_ROOT = Path(__file__).parent.parent.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

# Serve static files from frontend/dist/assets
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")
    
    # Serve other static files (images, etc.)
    for static_dir in ["images", "fonts", "icons"]:
        static_path = FRONTEND_DIST / static_dir
        if static_path.exists():
            app.mount(f"/{static_dir}", StaticFiles(directory=static_path), name=static_dir)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "carebridge-ai"}


# Serve index.html for root path
@app.get("/")
async def serve_root():
    if FRONTEND_DIST.exists():
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    return {"message": "Frontend not built. Run: cd frontend && npm run build"}


# SPA catch-all route - serve index.html for any non-API path
@app.get("/{path:path}")
async def serve_spa(path: str):
    # Skip API routes and static assets
    if path.startswith("api/") or path.startswith("assets/"):
        return {"detail": "Not Found"}
    
    if FRONTEND_DIST.exists():
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    return {"message": "Frontend not built. Run: cd frontend && npm run build"}
