from fastapi import FastAPI, Response, Depends
from confluent_kafka import Producer
import uuid
import json
import logging

from app.models import FeedbackForm, FeedbackCreatedResponse
from app.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

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
    producer: Producer = Depends(get_kafka_producer)
):
    feedback_id = uuid.uuid4()

    feedback_event = {
        "id": str(feedback_id),
        "text": form.text
    }

    producer.produce(
        settings.kafka_topic,
        key=feedback_id,
        value=json.dumps(feedback_event),
        callback=kafka_delivery_report
    )

    response.headers['Location'] = f'/feedbacks/{feedback_id}'
    return FeedbackCreatedResponse(id=feedback_id)
