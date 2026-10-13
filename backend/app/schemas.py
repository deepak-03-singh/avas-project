from pydantic import BaseModel, Field, ConfigDict, EmailStr

class RegisterInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserPublic(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic

class StartupInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    startup_name: str = Field(min_length=2, max_length=120)
    industry: str = Field(min_length=2, max_length=100)
    problem_clarity: int = Field(ge=1, le=5)
    solution_differentiation: int = Field(ge=1, le=5)
    market_demand: int = Field(ge=1, le=5)
    competition_intensity: int = Field(ge=1, le=5)
    founder_experience: int = Field(ge=1, le=5)
    team_completeness: int = Field(ge=1, le=5)
    traction_level: int = Field(ge=1, le=5)
    revenue_model_clarity: int = Field(ge=1, le=5)
    financial_runway_months: int = Field(ge=0, le=120)
    customer_validation_count: int = Field(ge=0, le=1000000)
    monthly_revenue: float = Field(ge=0, le=1_000_000_000_000)
    monthly_burn: float = Field(ge=0, le=1_000_000_000_000)
    funding_needed: float = Field(ge=0, le=10_000_000_000_000)
    target_market_size_millions: float = Field(ge=0, le=10_000_000_000_000)
    has_prototype: bool
    has_competitor_research: bool

class AssessmentResponse(BaseModel):
    id: int | None = None
    startup_name: str
    industry: str
    readiness_score: int
    score_band: str
    demonstration_success_probability: float | None
    probability_warning: str
    risk_level: str
    risk_flags: list[str]
    growth_potential_score: int
    growth_score_note: str
    explainability: dict
    swot: dict[str, list[str]]
    recommendations: list[str]
    factor_summary: dict[str, float]
    model_status: str
    created_at: str | None = None


class CompareInput(BaseModel):
    assessment_ids: list[int] = Field(min_length=2, max_length=4)
