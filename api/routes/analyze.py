from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.schemas import AnalyzeRequest, AnalyzeResponse
from database.models import SessionStatus
from database.repositories import update_instruction_session, upsert_user
from database.session import get_db
from services.vision_service import vision_service


router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_object(payload: AnalyzeRequest, db: Session = Depends(get_db)) -> dict:
    user = upsert_user(db, telegram_id=payload.user_id)
    if payload.session_id:
        update_instruction_session(
            db,
            payload.session_id,
            status=SessionStatus.analyzing.value,
            user_goal=payload.user_goal,
        )

    analysis = vision_service.analyze(payload.image_url, payload.user_goal)

    if payload.session_id:
        update_instruction_session(
            db,
            payload.session_id,
            status=(
                SessionStatus.waiting_clarification.value
                if analysis.get("needs_clarification")
                else SessionStatus.generating_instruction.value
            ),
            detected_object=analysis.get("detected_object"),
            confidence=analysis.get("confidence"),
            user_goal=payload.user_goal,
        )
    else:
        _ = user

    return analysis
