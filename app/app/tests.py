import uuid
from confluent_kafka import Message
from fastapi.testclient import TestClient
from app.main import app, get_kafka_producer
from app.models import FeedbackForm


class MockProducer:
    def __init__(self):
        self.messages = []

    def produce(self, topic, key, value, callback):
        msgmock = lambda: None

        setattr(msgmock, 'topic', lambda: topic)
        setattr(msgmock, 'key', lambda: key)
        setattr(msgmock, 'value', lambda: value)
        setattr(msgmock, 'partition', lambda: 0)
        callback(None, msgmock)

    def flush(self):
        pass

global_producer_mock = MockProducer()

def mock_get_kafka_producer():
    return global_producer_mock

app.dependency_overrides[get_kafka_producer] = mock_get_kafka_producer

client = TestClient(app)

def test_submit_feedback():
    feedback_form = FeedbackForm(
        text="This is a test feedback"
    )

    response = client.post("/feedbacks", json=feedback_form.model_dump())

    assert response.status_code == 201

    assert "Location" in response.headers
    location = response.headers["Location"]
    path, id, *_ = location.split("/")[1:]
    assert path == 'feedbacks'
    assert uuid.UUID(id)
    response_data = response.json()
    assert response_data["id"] == id


def test_submit_feedback_invalid_data():
    invalid_data = {
        "extra_field": "w some extra data",
        "message": 0xDEADBEEF
    }

    response = client.post("/feedbacks", json=invalid_data)

    assert response.status_code == 422
