from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str            
    MONGODB_DB_NAME: str       
    SECRET_KEY: str              
    GEMINI_API_KEY: str

    class Config:
        env_file = ".env copy"
        env_file_encoding = "utf-8"

settings = Settings()
