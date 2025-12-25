"""
Entry point для LangGraph Studio.
Экспортирует переменную `graph` для использования в Studio.
"""

import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Импорты после загрузки .env
from src.config import get_llm
from src.data_loader import load_price_list
from src.tools import create_tools
from src.agent import build_agent


# =============================================================================
# ИНИЦИАЛИЗАЦИЯ
# =============================================================================

logger.info("Инициализация ассистента автосервиса...")

# 1. Загружаем прайс-лист из Google Sheets
try:
    PRICE_LIST = load_price_list()
    logger.info(f"Прайс-лист загружен: {len(PRICE_LIST)} услуг")
except Exception as e:
    logger.error(f"Ошибка загрузки прайс-листа: {e}")
    raise

# 2. Создаём инструменты с привязкой к прайс-листу
tools = create_tools(PRICE_LIST)
logger.info(f"Инструменты инициализированы: {[t.name for t in tools]}")

# 3. Получаем LLM клиент
try:
    llm = get_llm()
    logger.info(f"LLM инициализирован: {llm.model_name}")
except Exception as e:
    logger.error(f"Ошибка инициализации LLM: {e}")
    raise

# 4. Создаём граф агента (без checkpointer - Studio добавит свой)
graph = build_agent(tools, llm)
logger.info("Граф агента создан и готов к работе")


# =============================================================================
# ЛОКАЛЬНЫЙ ТЕСТ
# =============================================================================

def test_locally():
    """Тестирует агента локально (без Studio)."""
    from pathlib import Path
    from langchain_core.messages import HumanMessage
    from langgraph.checkpoint.sqlite import SqliteSaver
    from src.config import CHECKPOINTS_DB

    print("=" * 60)
    print("Локальный тест ассистента автосервиса")
    print("=" * 60)

    # Создаём директорию для базы данных
    Path(CHECKPOINTS_DB).parent.mkdir(parents=True, exist_ok=True)

    # Создаём агент с persistence в SQLite
    with SqliteSaver.from_conn_string(CHECKPOINTS_DB) as checkpointer:
        local_graph = build_agent(tools, llm, checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "test-session"}}

        questions = [
            "Привет! Какие услуги у вас есть?",
            "Сколько стоит диагностика двигателя?",
            "А что по тормозам?",
            "Замена масла в двигателе - сколько?",
        ]

        for q in questions:
            print(f"\n{'─' * 40}")
            print(f"Клиент: {q}")

            result = local_graph.invoke(
                {"messages": [HumanMessage(content=q)]},
                config=config
            )

            print(f"Ассистент: {result['messages'][-1].content}")


if __name__ == "__main__":
    test_locally()
