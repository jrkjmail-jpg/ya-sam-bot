from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    bot_token: str = Field(default="", alias="BOT_TOKEN")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    database_url: str = Field(default="sqlite:///./yasam.db", alias="DATABASE_URL")
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_key: str = Field(default="", alias="SUPABASE_KEY")
    storage_bucket: str = Field(default="yasam", alias="STORAGE_BUCKET")
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")

    openai_text_model: str = Field(default="gpt-5-mini", alias="OPENAI_TEXT_MODEL")
    openai_image_model: str = Field(default="gpt-image-1", alias="OPENAI_IMAGE_MODEL")
    use_mock_ai: bool = Field(default=False, alias="USE_MOCK_AI")

    storage_dir: Path = Field(default=BASE_DIR / "storage", alias="STORAGE_DIR")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    @property
    def ai_is_mocked(self) -> bool:
        return self.use_mock_ai or not self.openai_api_key

    @property
    def effective_telegram_bot_token(self) -> str:
        return self.telegram_bot_token or self.bot_token

    @property
    def normalized_database_url(self) -> str:
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
