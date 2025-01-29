from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "feedback_events"
    kafka_group_id: str = "feedback_consumer_group"

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings()
