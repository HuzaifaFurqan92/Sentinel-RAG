from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Path(__file__).resolve().parent points directly to the 'app/' directory
APP_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    GROQ_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=APP_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()