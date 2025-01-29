from sqlalchemy import Column, String, UUID
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class Feedback(Base):
    __tablename__ = 'feedbacks'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(String, nullable=False)
