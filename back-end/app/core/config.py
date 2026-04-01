from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # trỏ về thư mục app/

class Settings(BaseSettings):
    # ─── App ───
    PROJECT_NAME: str = "Shore STT"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # ─── Groq / LLM ───
    GROQ_API_KEY: str | None = None
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ─── Conversation ───
    MAX_HISTORY_TURNS: int = 10
    SESSION_TTL_SEC: int = 1800

    # ─── STT / Audio ───
    SAMPLE_RATE: int = 16000

    # ─── TTS / Kokoro ───
    KOKORO_MODEL_PATH: str = str(BASE_DIR / "models/kokoro/kokoro-v1.0.onnx")
    KOKORO_VOICES_PATH: str = str(BASE_DIR / "models/kokoro/voices-v1.0.bin")
    KOKORO_VOICE: str = "af_heart"   # giọng Mỹ nữ, tự nhiên nhất
    KOKORO_SPEED: float = 1.0
    KOKORO_SAMPLE_RATE: int = 24000  # output sample rate của Kokoro

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

settings = Settings()