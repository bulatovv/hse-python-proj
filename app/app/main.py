import uuid
import json
import logging
from typing import Annotated
from fastapi import FastAPI, HTTPException, Response, Depends
from confluent_kafka import Producer
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram

from app.database import SessionLocal, engine
from app.db_models import Feedback, Base
from app.models import FeedbackForm, FeedbackCreatedResponse, FeedbackResponse
from app.settings import settings

logging.basicConfig(level=logging.INFO)
logger = None 

Base.metadata.create_all(bind=engine)

app = FastAPI()

REQUEST_COUNT = Counter(
    'app_request_count', 'Total number of requests', ['method', 'endpoint']
)
REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds', 'Request latency in seconds', ['method', 'endpoint']
)

@app.on_event("startup")
def setup_logger():
    global logger
    logger = logging.getLogger('uvicorn.error')

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
    global logger
    if logger is None:
        logger = logging.getLogger(__name__)

    if err is not None:
        logger.error(f"Message delivery failed: {err}") # type: ignore
    else:
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]") # type: ignore

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

@app.get('/feedbacks/{feedback_id}', response_model=FeedbackResponse)
def get_feedback(
    feedback_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)]
):
    db_feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if db_feedback is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return FeedbackResponse(id=db_feedback.id, text=db_feedback.text) # type: ignore

Instrumentator().instrument(app).expose(app)
