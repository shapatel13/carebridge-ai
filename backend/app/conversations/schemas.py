from pydantic import BaseModel


class ConversationCreate(BaseModel):
    patient_alias: str = "Patient A"
    tone_setting: str = "neutral"
    risk_calibration: float = 0.5
    participants: list[str] | None = None
    organ_supports: list[str] | None = None
    code_status_discussed: bool = False
    family_present: bool = False
    language: str = "english"
    code_status_change: str | None = None
    surrogate_name: str | None = None
    surrogate_relationship: str | None = None
    family_questions: list[str] | None = None
    clinician_annotations: list[str] | None = None


class ConversationUpdate(BaseModel):
    patient_alias: str | None = None
    tone_setting: str | None = None
    risk_calibration: float | None = None
    participants: list[str] | None = None
    organ_supports: list[str] | None = None
    code_status_discussed: bool | None = None
    family_present: bool | None = None
    language: str | None = None
    code_status_change: str | None = None
    surrogate_name: str | None = None
    surrogate_relationship: str | None = None
    family_questions: list[str] | None = None
    clinician_annotations: list[str] | None = None


class SegmentCreate(BaseModel):
    text: str
    confidence: float = 1.0


class GenerateRequest(BaseModel):
    pass


class ConversationResponse(BaseModel):
    id: str
    patient_alias: str
    physician_id: str
    hospital_id: str
    status: str
    tone_setting: str
    risk_calibration: float
    participants: list[str] | None = None
    organ_supports: list[str] | None = None
    code_status_discussed: bool
    family_present: bool = False
    language: str = "english"
    code_status_change: str | None = None
    surrogate_name: str | None = None
    surrogate_relationship: str | None = None
    family_questions: list[str] | None = None
    clinician_annotations: list[str] | None = None
    created_at: str
    finalized_at: str | None = None

    model_config = {"from_attributes": True}


class SegmentResponse(BaseModel):
    id: str
    text: str
    confidence: float
    segment_order: int

    model_config = {"from_attributes": True}


class PhysicianNote(BaseModel):
    participants: str = ""
    medical_status_explained: str = ""
    prognosis_discussed: str = ""
    uncertainty_addressed: str = ""
    family_understanding_noted: str = ""
    code_status: str = ""
    surrogate_decision_maker: str = ""


class RiskFlag(BaseModel):
    type: str
    severity: str  # "yellow" or "red"
    message: str
    suggestion: str


class GeneratedOutputResponse(BaseModel):
    id: str
    conversation_id: str
    physician_note: dict
    family_summary: str
    risk_flags: list[dict]
    created_at: str

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    conversation: ConversationResponse
    segments: list[SegmentResponse]
    output: GeneratedOutputResponse | None = None
