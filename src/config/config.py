from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class ModelConfig:
    large_model: str = os.getenv("LARGE_MODEL", "ollama:llama3.1:8b")
    small_model: str = os.getenv("SMALL_MODEL", "ollama:granite4:micro-h")
    fin_model: str = os.getenv("FIN_MODEL", "ollama:0xroyce/Plutus-3B:latest")
    default_timeout: int = int(os.getenv("DEFAULT_TIMEOUT", "12000"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    llm_timeout: int = int(os.getenv("AGENT_TIMEOUT", "6000"))
    main_llm_timeout: int = int(os.getenv("MAIN_AGENT_TIMEOUT", "9000"))


@dataclass
class AppConfig:
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    cache_duration_minutes: int = int(os.getenv("CACHE_DURATION", "15"))


config = ModelConfig()
app_config = AppConfig()

