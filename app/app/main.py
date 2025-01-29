import uuid
import json
import logging
from typing import Annotated
from fastapi import FastAPI, Response, Depends
from confluent_kafka import Producer
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.db_models import Feedback
from app.models import FeedbackForm, FeedbackCreatedResponse
from app.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


Feedback.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_kafka_producer():
    producer = Producer({
        "bootstrap.servers": settings.kafka_bootstrap_servers
    })
    try:
        yield producer
    finally:
        producer.flush()

def kafka_delivery_report(err, msg):
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")


@app.post('/feedbacks', status_code=201)
def submit_feedback(
    form: FeedbackForm,
    response: Response,
    producer: Annotated[Producer, Depends(get_kafka_producer)],
    db: Annotated[Session, Depends(get_db)] 
):
    feedback_id = uuid.uuid4()

    db_feedback = Feedback(id=feedback_id, text=form.text)
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)

    feedback_event = {
        "id": str(feedback_id),
        "text": form.text
    }

    producer.produce(
        settings.kafka_topic,
        key=str(feedback_id).encode('utf-8'),
        value=json.dumps(feedback_event),
        callback=kafka_delivery_report
    )

    response.headers['Location'] = f'/feedbacks/{feedback_id}'
    return FeedbackCreatedResponse(id=feedback_id)
