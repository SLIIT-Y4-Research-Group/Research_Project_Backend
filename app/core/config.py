from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str              # must match env key exactly
    MONGODB_DB_NAME: str          # must match env key exactly
    SECRET_KEY: str               # optional if your code uses it

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
