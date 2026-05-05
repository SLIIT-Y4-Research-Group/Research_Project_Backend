from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URI: str = Field(alias="MONGO_URI")
    MONGODB_DB_NAME: str = Field(alias="MONGO_DB_NAME")

    # Security
    SECRET_KEY: str

    # Gemini
    # GEMINI_API_KEY: str = Field(alias="STORY_GEMINI_API_KEY")
    GEMINI_API_KEYS: List[str] = Field(alias="STORY_GEMINI_API_KEYS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()