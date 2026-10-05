import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def get_default_output_dir() -> str:
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
        return "/tmp/output"
    base_out = os.path.join(BASE_DIR, "output")
    try:
        os.makedirs(base_out, exist_ok=True)
        test_file = os.path.join(base_out, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return base_out
    except Exception:
        return "/tmp/output"

def get_default_data_dir() -> str:
    base_data = os.path.join(BASE_DIR, "data")
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
        return "/tmp/data"
    try:
        os.makedirs(base_data, exist_ok=True)
        return base_data
    except Exception:
        return "/tmp/data"

class Settings(BaseSettings):
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_BASE_URL: str = ""
    DATA_DIR: str = get_default_data_dir()
    OUTPUT_DIR: str = get_default_output_dir()
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist safely (handling serverless read-only filesystems gracefully)
for d in [
    os.path.join(settings.DATA_DIR, "raw"),
    os.path.join(settings.DATA_DIR, "processed"),
    os.path.join(settings.OUTPUT_DIR, "observations"),
    os.path.join(settings.OUTPUT_DIR, "clusters"),
    os.path.join(settings.OUTPUT_DIR, "opportunities")
]:
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass


