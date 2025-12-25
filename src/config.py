"""
Конфигурация приложения: LLM, модели данных, константы.
"""

import os
from typing import Optional

from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel


# =============================================================================
# КОНСТАНТЫ
# =============================================================================

# Google Sheets URL для скачивания прайс-листа
GOOGLE_SHEETS_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1YVoGrN5P1I7IM_gK5shtfenS70GG6-zj8HqiGHq5-Zc/"
    "export?format=csv&gid=2146139797"
)

# Путь к базе данных SQLite для checkpoints
CHECKPOINTS_DB = "data/checkpoints.db"


# =============================================================================
# МОДЕЛИ ДАННЫХ
# =============================================================================

class Service(BaseModel):
    """Модель услуги автосервиса."""
    category: str
    name: str
    price: float
    note: Optional[str] = None


# =============================================================================
# LLM КОНФИГУРАЦИЯ
# =============================================================================

def get_llm(
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> BaseChatModel:
    """
    Создаёт LLM клиент с поддержкой любого OpenAI-совместимого API.
    """
    model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
    base_url = base_url or os.getenv("LLM_BASE_URL")
    api_key = api_key or os.getenv("LLM_API_KEY")

    if not api_key:
        raise ValueError("LLM_API_KEY не найден в переменных окружения")

    return ChatOpenAI(
        model=model,
        base_url=base_url,  # None = стандартный OpenAI API
        api_key=api_key,
        temperature=0,
    )
