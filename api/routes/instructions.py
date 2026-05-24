from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.schemas import (
    GenerateInstructionRequest,
    GenerateInstructionResponse,
    InstructionHistoryItem,
)
from database.models import SessionStatus
from database.repositories import (
    create_instruction,
    list_user_instructions,
    update_instruction_session,
    upsert_user,
)
from database.session import get_db
from services.instruction_service import instruction_service


router = APIRouter(tags=["instructions"])


@router.post("/generate-instruction", response_model=GenerateInstructionResponse)
def generate_instruction(payload: GenerateInstructionRequest, db: Session = Depends(get_db)) -> dict:
    user = upsert_user(db, telegram_id=payload.user_id)
    if payload.session_id:
        update_instruction_session(
            db,
            payload.session_id,
            status=SessionStatus.generating_instruction.value,
            user_goal=payload.user_goal,
        )

    instruction = instruction_service.generate(
        payload.image_url,
        payload.user_goal,
        payload.confirmed_details,
    )

    if payload.session_id:
        create_instruction(
            db,
            session_id=payload.session_id,
            title=instruction["title"],
            short_summary=instruction["short_summary"],
            steps=instruction["steps"],
        )
        update_instruction_session(db, payload.session_id, status=SessionStatus.generating_images.value)
        instruction["session_id"] = payload.session_id
    else:
        _ = user

    return instruction


@router.get("/instructions/{user_id}", response_model=list[InstructionHistoryItem])
def instructions_history(user_id: int, db: Session = Depends(get_db)) -> list[dict]:
    user = upsert_user(db, telegram_id=user_id)
    items = list_user_instructions(db, user.id)
    return [
        {
            "id": item.id,
            "title": item.title,
            "short_summary": item.short_summary,
            "collage_url": item.collage_url,
            "created_at": item.created_at.isoformat(),
        }
        for item in items
    ]
