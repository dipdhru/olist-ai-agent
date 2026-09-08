import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMConfig:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"
    temperature: float = 0.0
    max_tokens: int = 1000

def load_config() -> LLMConfig:
    return LLMConfig(
        api_key=os.getenv("LLM_API_KEY", "your-api-key-here"),
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("LLM_MODEL", "gpt-4o"),
    )
