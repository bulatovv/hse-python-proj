from confluent_kafka import Consumer, KafkaError, KafkaException
import json
import logging
import sys

from ml.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_kafka_consumer():
    consumer_config = {
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "group.id": settings.kafka_group_id,
        "auto.offset.reset": "latest",
        "enable.auto.commit": False,
    }
    return Consumer(consumer_config)

def process_feedback_event(feedback_event):
    logger.info(f"Processing feedback event: {feedback_event}")

def consume_feedback_events():
    consumer = create_kafka_consumer()
    consumer.subscribe([settings.kafka_topic])

    logger.info("Starting Kafka consumer...")
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue

            if not msg.error():
                try:
                    feedback_event = json.loads(msg.value().decode("utf-8"))
                    process_feedback_event(feedback_event)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
            else:
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.info(f"Reached end of partition {msg.partition()}")
                elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    logger.error(f"Topic or partition does not exist: {msg.topic()}[{msg.partition()}]")
                    sys.exit(1)
                elif msg.error():
                    raise KafkaException(msg.error())

                consumer.commit(asynchronous=False)

    except KeyboardInterrupt:
        logger.info("Shutting down Kafka consumer...")
    finally:
        consumer.close()

if __name__ == "__main__":
    consume_feedback_events()
