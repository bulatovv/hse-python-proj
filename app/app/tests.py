import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app, get_kafka_producer, get_db
from app.models import FeedbackForm
from app.database import SessionLocal, engine
from app.db_models import Feedback, Base



def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

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
app.dependency_overrides[get_db] = override_get_db

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

    db = next(override_get_db())
    feedback = db.query(Feedback).filter(Feedback.id == uuid.UUID(id)).first()
    assert feedback is not None
    assert feedback.text == "This is a test feedback" # type: ignore

def test_submit_feedback_invalid_data():
    invalid_data = {
        "extra_field": "w some extra data",
        "message": 0xDEADBEEF
    }

    response = client.post("/feedbacks", json=invalid_data)

    assert response.status_code == 422

def test_get_feedback_exists():
    feedback_form = FeedbackForm(text="Test feedback")
    post_response = client.post("/feedbacks", json=feedback_form.model_dump())
    assert post_response.status_code == 201

    feedback_id = post_response.json()["id"]

    get_response = client.get(f"/feedbacks/{feedback_id}")
    assert get_response.status_code == 200

    response_data = get_response.json()
    assert response_data["id"] == feedback_id
    assert response_data["text"] == "Test feedback"


def test_get_feedback_not_exists():
    non_existent_feedback_id = uuid.uuid4()

    get_response = client.get(f"/feedbacks/{non_existent_feedback_id}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Feedback not found"


def test_get_feedback_invalid_uuid():
    invalid_uuid = "not-a-valid-uuid"

    get_response = client.get(f"/feedbacks/{invalid_uuid}")
    assert get_response.status_code == 422
