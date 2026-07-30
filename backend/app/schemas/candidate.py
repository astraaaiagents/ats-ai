from pydantic import BaseModel, field_validator


class CandidateSkillInput(BaseModel):
    skill_name: str
    proficiency: int | str | None = None
    years_experience: float | None = None

    @field_validator("proficiency", mode="before")
    @classmethod
    def parse_proficiency(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            if v.isdigit():
                return int(v)
            mapping = {"beginner": 1, "junior": 2, "intermediate": 3, "advanced": 4, "expert": 5}
            return mapping.get(v.lower(), 3)
        return v


class CandidateSkillResponse(BaseModel):
    id: str
    skill_name: str
    proficiency: int | None
    years_experience: float | None

    model_config = {"from_attributes": True}


class CandidateDocumentResponse(BaseModel):
    id: str
    document_type: str
    file_name: str
    file_size_bytes: int
    s3_key: str
    created_at: str

    model_config = {"from_attributes": True}


class CandidateTimelineEvent(BaseModel):
    id: str
    event_type: str
    description: str | None
    metadata: dict | None
    created_at: str

    model_config = {"from_attributes": True}


class CandidateCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    current_title: str | None = None
    current_employer: str | None = None
    location: str | None = None
    salary_expectation_min: int | None = None
    salary_expectation_max: int | None = None
    visa_status: str | None = None
    notice_period_days: int | None = None
    source: str | None = None
    status: str | None = None
    ai_summary: str | None = None
    skills: list[CandidateSkillInput] = []


class CandidateUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    current_title: str | None = None
    current_employer: str | None = None
    location: str | None = None
    salary_expectation_min: int | None = None
    salary_expectation_max: int | None = None
    visa_status: str | None = None
    notice_period_days: int | None = None
    source: str | None = None


class CandidateStatusUpdate(BaseModel):
    status: str
    reason: str | None = None


class CandidateResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    current_title: str | None
    current_employer: str | None
    location: str | None
    salary_expectation_min: int | None
    salary_expectation_max: int | None
    visa_status: str | None
    notice_period_days: int | None
    source: str | None
    status: str
    owner_id: str | None
    ai_summary: str | None
    ai_summary_generated_at: str | None
    is_ai_summary_edited: bool
    skills: list[CandidateSkillResponse] = []
    documents: list[CandidateDocumentResponse] = []
    timeline: list[CandidateTimelineEvent] = []
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class DedupCheckRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class DedupCheckResponse(BaseModel):
    is_duplicate: bool
    candidates: list[dict] = []
