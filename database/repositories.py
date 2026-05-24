from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from database.models import Instruction, InstructionSession, SessionStatus, StoredImage, User


def upsert_user(db: Session, telegram_id: int, username: str | None = None) -> User:
    user = db.scalar(select(User).where(User.telegram_id == telegram_id))
    if user:
        if username and user.username != username:
            user.username = username
            db.commit()
            db.refresh(user)
        return user

    user = User(telegram_id=telegram_id, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_instruction_session(db: Session, user_id: int, status: str = SessionStatus.waiting_goal.value) -> InstructionSession:
    session = InstructionSession(user_id=user_id, status=status)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_instruction_session(db: Session, session_id: int, **values) -> InstructionSession | None:
    session = db.get(InstructionSession, session_id)
    if not session:
        return None
    for key, value in values.items():
        setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return session


def add_image(db: Session, session_id: int, image_type: str, url: str) -> StoredImage:
    image = StoredImage(session_id=session_id, type=image_type, url=url)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def create_instruction(
    db: Session,
    session_id: int,
    title: str,
    short_summary: str,
    steps: list[dict],
    collage_url: str | None = None,
) -> Instruction:
    instruction = Instruction(
        session_id=session_id,
        title=title,
        short_summary=short_summary,
        json_steps=steps,
        collage_url=collage_url,
    )
    db.add(instruction)
    db.commit()
    db.refresh(instruction)
    return instruction


def set_instruction_collage(db: Session, session_id: int, collage_url: str) -> Instruction | None:
    instruction = db.scalar(select(Instruction).where(Instruction.session_id == session_id))
    if not instruction:
        return None
    instruction.collage_url = collage_url
    db.commit()
    db.refresh(instruction)
    return instruction


def list_user_instructions(db: Session, user_id: int, limit: int = 20) -> list[Instruction]:
    query = (
        select(Instruction)
        .join(InstructionSession)
        .where(InstructionSession.user_id == user_id)
        .order_by(desc(Instruction.created_at))
        .limit(limit)
    )
    return list(db.scalars(query))
