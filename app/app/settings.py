from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "feedback_events"
    database_url: str = 'sqlite:///file:app?mode=memory&cache=shared'

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings()
