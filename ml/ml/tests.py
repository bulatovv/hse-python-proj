import json
from confluent_kafka import KafkaError
import pytest

from ml import feedback_consumer

class MockConsumer:
    def __init__(self):
        self.messages = []
        self.subscribed_topics = []

    def subscribe(self, topics):
        self.subscribed_topics = topics

    def poll(self, timeout=1.0):
        if self.messages:
            return self.messages.pop(0)
        else:
            raise KeyboardInterrupt()

    def commit(self, asynchronous=False):
        pass

    def close(self):
        pass

class MockMessage:
    def __init__(self, value, error=None):
        self._value = value
        self._error = error

    def error(self):
        return self._error

    def value(self):
        return self._value
    
    def topic(self):
        return 'topic'
    
    def partition(self):
        return 0

class MockKafkaError:
    def __init__(self, code):
        self._code = code

    def code(self):
        return self._code

@pytest.fixture
def mock_consumer():
    return MockConsumer()

@pytest.fixture
def mock_message():
    return MockMessage(json.dumps({"feedback": "test feedback"}).encode("utf-8"))

def test_consume_feedback_events(mock_consumer, mock_message, caplog):
    mock_consumer.messages = [mock_message]
    

    feedback_consumer.create_kafka_consumer = lambda: mock_consumer
    feedback_consumer.consume_feedback_events()

    assert "Processing feedback event: {'feedback': 'test feedback'}" in caplog.text

def test_consume_feedback_events_json_decode_error(mock_consumer, caplog):
    mock_consumer.messages = [MockMessage(b"invalid json")]

    feedback_consumer.create_kafka_consumer = lambda: mock_consumer
    feedback_consumer.consume_feedback_events()

    assert "Failed to decode message:" in caplog.text

def test_consume_feedback_events_kafka_error(mock_consumer, caplog):
    mock_error = MockKafkaError(KafkaError(error=KafkaError.UNKNOWN_TOPIC_OR_PART))
    mock_consumer.messages = [MockMessage(None, error=mock_error)]

    feedback_consumer.create_kafka_consumer = lambda: mock_consumer

    with pytest.raises(SystemExit):
        feedback_consumer.consume_feedback_events()

    assert "Topic or partition does not exist:" in caplog.text
