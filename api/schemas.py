from pydantic import BaseModel, Field


class UploadImageResponse(BaseModel):
    image_url: str
    session_id: int


class AnalyzeRequest(BaseModel):
    user_id: int
    image_url: str
    user_goal: str
    session_id: int | None = None


class AnalyzeResponse(BaseModel):
    detected_object: str
    user_goal: str
    confidence: float = Field(ge=0, le=1)
    important_visible_parts: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    needs_clarification: bool
    clarification_question: str | None = None
    can_generate_instruction: bool


class InstructionStep(BaseModel):
    step_number: int
    title: str
    description: str
    visual_prompt: str


class GenerateInstructionRequest(BaseModel):
    user_id: int
    image_url: str
    user_goal: str
    confirmed_details: str | None = None
    session_id: int | None = None


class GenerateInstructionResponse(BaseModel):
    title: str
    short_summary: str
    safety_notes: list[str] = Field(default_factory=list)
    steps: list[InstructionStep]
    session_id: int | None = None


class GenerateImagesRequest(BaseModel):
    user_id: int
    image_url: str
    instruction: GenerateInstructionResponse
    session_id: int | None = None


class StepImage(BaseModel):
    step_number: int
    image_url: str


class GenerateImagesResponse(BaseModel):
    step_images: list[StepImage]


class CreateCollageRequest(BaseModel):
    user_id: int
    title: str
    object_image_url: str
    step_images: list[StepImage]
    session_id: int | None = None


class CreateCollageResponse(BaseModel):
    collage_url: str


class InstructionHistoryItem(BaseModel):
    id: int
    title: str
    short_summary: str
    collage_url: str | None = None
    created_at: str
