from typing import Literal, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator
CareType = Literal["paramedic_home_visit", "home_nursing", "lab_test_home", "teleconsultation", "emergency_112"]
Urgency = Literal["same_day", "scheduled", "emergency"]
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
class Location(StrictModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
class HistoryMessage(StrictModel):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=5000)
class TriageRequest(StrictModel):
    user_input: str = Field(min_length=1, max_length=5000)
    language: Literal["auto", "English", "Hindi", "Hinglish"] = "auto"
    location: Location | None = None
    conversation_history: list[HistoryMessage] = Field(default_factory=list, max_length=40)
class Match(StrictModel):
    caregiver_id: str
    score: float = Field(ge=0, le=1)
    reason: str
class TriageResponse(StrictModel):
    follow_up_question: str | None
    care_type: CareType | None
    urgency: Urgency | None
    red_flags: list[str]
    reasoning: str
    matched_caregivers: list[Match]
    @model_validator(mode="after")
    def check_flow(self):
        if self.follow_up_question is not None:
            if self.care_type is not None or self.urgency is not None or self.matched_caregivers:
                raise ValueError("Clarification cannot contain a final decision or matches")
        elif self.care_type is None or self.urgency is None:
            raise ValueError("A final decision requires care type and urgency")
        if self.red_flags or self.care_type == "emergency_112" or self.urgency == "emergency":
            if self.care_type != "emergency_112" or self.urgency != "emergency" or self.matched_caregivers:
                raise ValueError("Emergency must bypass matching")
        return self

class AssistantChatRequest(StrictModel):
    message: str = Field(default="", max_length=10000)
    language: Literal["auto", "English", "Hindi", "Hinglish"] = "auto"
    location: Location | None = None
    image_base64: str | None = None
    image_mime_type: str | None = None

    @model_validator(mode="after")
    def validate_content(self):
        if not self.message.strip() and not self.image_base64:
            raise ValueError("Either message text or an uploaded image is required.")
        return self

class AssistantFactsCorrectionRequest(StrictModel):
    facts: dict[str, Any]

