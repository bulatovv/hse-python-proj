from uuid import UUID
from pydantic import BaseModel

class FeedbackForm(BaseModel):
    text: str


class FeedbackCreatedResponse(BaseModel):
    id: UUID
