import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./pe_assessment.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    GROQ_API_KEY: str = ""
    MODEL_DIR: str = "models"
    DATA_DIR: str = "data"
    SPARK_MASTER: str = "local[*]"
    
    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
