from pydantic import BaseModel, Field


class UploadImageResponse(BaseModel):
    image_url: str
    session_id: int


class AnalyzeRequest(BaseModel):
    user_id: int
    image_url: str
    image_urls: list[str] | None = None
    user_goal: str
    session_id: int | None = None


class IdentifyObjectRequest(BaseModel):
    user_id: int
    image_url: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    session_id: int | None = None


class AnalyzeResponse(BaseModel):
    detected_object: str
    object_category: str | None = None
    brand: str | None = None
    model: str | None = None
    product_name: str | None = None
    match_status: str | None = None
    exact_match_confidence: float | None = Field(default=None, ge=0, le=1)
    candidate_models: list[str] = Field(default_factory=list)
    object_signature: str | None = None
    visual_reference_prompt: str | None = None
    real_instruction_summary: str | None = None
    source_notes: list[str] = Field(default_factory=list)
    user_goal: str
    confidence: float = Field(ge=0, le=1)
    visible_parts: list[str] = Field(default_factory=list)
    important_parts: list[str] = Field(default_factory=list)
    important_visible_parts: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    needs_clarification: bool
    clarification_question: str | None = None
    can_generate_instruction: bool
    service_error: str | None = None


class VisualSpec(BaseModel):
    main_object: str | None = None
    scene: str | None = None
    composition: str | None = None
    required_elements: list[str] = Field(default_factory=list)
    action: str | None = None
    highlight: str | None = None
    avoid: list[str] = Field(default_factory=list)


class InstructionStep(BaseModel):
    step_number: int
    title: str
    description: str
    action_type: str | None = None
    focus_area: str | None = None
    camera_angle: str | None = None
    hand_action: str | None = None
    visual_highlight: str | None = None
    state_before: str | None = None
    state_after: str | None = None
    visual_spec: VisualSpec | None = None
    image_prompt: str | None = None
    visual_prompt: str = ""


class GenerateInstructionRequest(BaseModel):
    user_id: int
    image_url: str
    user_goal: str
    analysis: dict | None = None
    confirmed_details: str | None = None
    session_id: int | None = None


class GenerateInstructionResponse(BaseModel):
    title: str
    short_summary: str
    instruction_target: str | None = None
    object_reference: dict | None = None
    suitable_for: str | None = None
    safety_notes: list[str] = Field(default_factory=list)
    steps: list[InstructionStep]
    extra_sections: list[dict] = Field(default_factory=list)
    quality_check: dict | None = None
    session_id: int | None = None
    service_error: str | None = None


class GenerateImagesRequest(BaseModel):
    user_id: int
    image_url: str
    instruction: GenerateInstructionResponse | None = None
    instruction_plan: GenerateInstructionResponse | None = None
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
    instruction_plan: GenerateInstructionResponse | None = None
    session_id: int | None = None


class CreateCollageResponse(BaseModel):
    collage_url: str


class InstructionHistoryItem(BaseModel):
    id: int
    title: str
    short_summary: str
    collage_url: str | None = None
    created_at: str
