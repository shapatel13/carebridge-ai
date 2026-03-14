import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ConversationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    FINALIZED = "FINALIZED"


class ToneSetting(str, enum.Enum):
    OPTIMISTIC = "optimistic"
    NEUTRAL = "neutral"
    CONCERNED = "concerned"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_alias: Mapped[str] = mapped_column(String(255), default="Patient A")
    physician_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    hospital_id: Mapped[str] = mapped_column(String(36), ForeignKey("hospitals.id"), nullable=False)
    status: Mapped[ConversationStatus] = mapped_column(Enum(ConversationStatus), default=ConversationStatus.DRAFT)
    tone_setting: Mapped[ToneSetting] = mapped_column(Enum(ToneSetting), default=ToneSetting.NEUTRAL)
    risk_calibration: Mapped[float] = mapped_column(Float, default=0.5)

    participants: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    organ_supports: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    code_status_discussed: Mapped[bool] = mapped_column(Boolean, default=False)
    family_present: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String(20), default="english")
    code_status_change: Mapped[str | None] = mapped_column(String(255), nullable=True)
    surrogate_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    surrogate_relationship: Mapped[str | None] = mapped_column(String(255), nullable=True)
    family_questions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    clinician_annotations: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    segments: Mapped[list["ConversationSegment"]] = relationship("ConversationSegment", back_populates="conversation", order_by="ConversationSegment.segment_order")
    output: Mapped["GeneratedOutput | None"] = relationship("GeneratedOutput", back_populates="conversation", uselist=False)


class ConversationSegment(Base):
    __tablename__ = "conversation_segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    segment_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="segments")


class GeneratedOutput(Base):
    __tablename__ = "generated_outputs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), unique=True, nullable=False)
    physician_note: Mapped[dict] = mapped_column(JSON, nullable=False)
    family_summary: Mapped[str] = mapped_column(Text, nullable=False)
    readability_grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_flags: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    ai_insights: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="output")
