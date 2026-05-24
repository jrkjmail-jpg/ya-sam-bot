from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class SessionStatus(StrEnum):
    waiting_photo = "waiting_photo"
    waiting_goal = "waiting_goal"
    analyzing = "analyzing"
    waiting_clarification = "waiting_clarification"
    generating_instruction = "generating_instruction"
    generating_images = "generating_images"
    completed = "completed"
    failed = "failed"


class StoredImageType(StrEnum):
    source_photo = "source_photo"
    clarification_photo = "clarification_photo"
    step_card = "step_card"
    collage = "collage"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("telegram_id", name="uq_users_telegram_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    sessions: Mapped[list["InstructionSession"]] = relationship(back_populates="user")


class InstructionSession(Base):
    __tablename__ = "instruction_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), default=SessionStatus.waiting_photo.value, nullable=False)
    user_goal: Mapped[str | None] = mapped_column(Text)
    detected_object: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="sessions")
    images: Mapped[list["StoredImage"]] = relationship(back_populates="session")
    instruction: Mapped["Instruction | None"] = relationship(back_populates="session")


class StoredImage(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("instruction_sessions.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    session: Mapped[InstructionSession] = relationship(back_populates="images")


class Instruction(Base):
    __tablename__ = "instructions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("instruction_sessions.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_summary: Mapped[str] = mapped_column(Text, nullable=False)
    json_steps: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    collage_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    session: Mapped[InstructionSession] = relationship(back_populates="instruction")
