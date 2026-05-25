from pathlib import Path
import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from api.schemas import (
    CreateCollageRequest,
    CreateCollageResponse,
    GenerateImagesRequest,
    GenerateImagesResponse,
    UploadImageResponse,
)
from database.models import SessionStatus, StoredImageType
from database.repositories import (
    add_image,
    create_instruction_session,
    set_instruction_collage,
    update_instruction_session,
    upsert_user,
)
from database.session import get_db
from services.collage_service import collage_service
from services.image_generation_service import image_generation_service
from services.storage_service import storage_service


router = APIRouter(tags=["images"])
logger = logging.getLogger(__name__)


@router.post("/upload-image", response_model=UploadImageResponse)
async def upload_image(
    user_id: int = Form(...),
    image_type: str = Form(StoredImageType.source_photo.value),
    session_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    user = upsert_user(db, telegram_id=user_id)
    if session_id is None:
        session = create_instruction_session(db, user_id=user.id, status=SessionStatus.waiting_goal.value)
        session_id = session.id

    suffix = Path(file.filename or "photo.jpg").suffix or ".jpg"
    image_url = storage_service.save_bytes(await file.read(), "photos", suffix)
    add_image(db, session_id=session_id, image_type=image_type, url=image_url)
    return {"image_url": image_url, "session_id": session_id}


@router.post("/generate-images", response_model=GenerateImagesResponse)
def generate_images(payload: GenerateImagesRequest, db: Session = Depends(get_db)) -> dict:
    if payload.session_id:
        update_instruction_session(db, payload.session_id, status=SessionStatus.generating_images.value)

    instruction = payload.instruction_plan or payload.instruction
    if instruction is None:
        return {"step_images": []}

    steps = [step.model_dump() for step in instruction.steps]
    step_images = image_generation_service.generate_step_images(payload.image_url, steps)

    if payload.session_id:
        for item in step_images:
            add_image(db, payload.session_id, StoredImageType.step_card.value, item["image_url"])

    return {"step_images": step_images}


@router.post("/generate-step-images", response_model=GenerateImagesResponse)
def generate_step_images(payload: GenerateImagesRequest, db: Session = Depends(get_db)) -> dict:
    return generate_images(payload, db)


@router.post("/create-collage", response_model=CreateCollageResponse)
def create_collage(payload: CreateCollageRequest, db: Session = Depends(get_db)) -> dict:
    step_images = [item.model_dump() for item in payload.step_images]
    collage_url = collage_service.create_collage(
        payload.title,
        step_images,
        instruction_plan=payload.instruction_plan.model_dump() if payload.instruction_plan else None,
        original_image_url=payload.object_image_url,
    )

    if payload.session_id:
        add_image(db, payload.session_id, StoredImageType.collage.value, collage_url)
        set_instruction_collage(db, payload.session_id, collage_url)
        update_instruction_session(db, payload.session_id, status=SessionStatus.completed.value)

    return {"collage_url": collage_url}


@router.post("/compose-instruction", response_model=CreateCollageResponse)
def compose_instruction(payload: CreateCollageRequest, db: Session = Depends(get_db)) -> dict:
    return create_collage(payload, db)
