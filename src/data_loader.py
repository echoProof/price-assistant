"""
Загрузка прайс-листа из Google Sheets.
"""

import csv
import io
import logging
from typing import Optional

import httpx

from src.config import Service, GOOGLE_SHEETS_URL

logger = logging.getLogger(__name__)


def load_from_google_sheets(url: str = GOOGLE_SHEETS_URL) -> Optional[list[Service]]:
    """
    Загружает прайс-лист из Google Sheets (CSV экспорт).

    Args:
        url: URL для скачивания CSV

    Returns:
        Список услуг или None при ошибке
    """
    try:
        logger.info("Загрузка прайс-листа из Google Sheets...")
        response = httpx.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()

        # Парсим CSV
        content = response.text
        reader = csv.reader(io.StringIO(content))

        services = []
        current_category = None

        for i, row in enumerate(reader):
            # Пропускаем заголовок
            if i == 0:
                continue

            # Пропускаем пустые строки
            if not row or len(row) < 3:
                continue

            category, name, price, *rest = row + [None]  # Добавляем None для note

            # Пропускаем строки без названия или цены
            if not name or not price:
                continue

            # Обработка "наследования" категории
            if category and category.strip():
                current_category = category.strip()

            # Парсим цену
            try:
                price_value = float(price.replace(",", ".").replace(" ", ""))
            except (ValueError, AttributeError):
                logger.warning(f"Не удалось распарсить цену: {price}")
                continue

            note = rest[0].strip() if rest and rest[0] else None

            services.append(Service(
                category=current_category or "Без категории",
                name=name.strip(),
                price=price_value,
                note=note,
            ))

        logger.info(f"Загружено {len(services)} услуг из Google Sheets")
        return services

    except Exception as e:
        logger.error(f"Ошибка загрузки из Google Sheets: {e}")
        return None


def load_price_list() -> list[Service]:
    """
    Загружает прайс-лист из Google Sheets.

    Returns:
        Список услуг

    Raises:
        RuntimeError: Если не удалось загрузить данные
    """
    services = load_from_google_sheets()
    if services:
        return services

    raise RuntimeError("Не удалось загрузить прайс-лист из Google Sheets")


def get_categories(services: list[Service]) -> list[str]:
    """Возвращает список уникальных категорий."""
    return sorted(set(s.category for s in services))


if __name__ == "__main__":
    # Тест загрузки
    logging.basicConfig(level=logging.INFO)

    print("Тестирование загрузки прайс-листа...")
    services = load_price_list()

    print(f"\nЗагружено {len(services)} услуг")
    print(f"Категории: {get_categories(services)}")

    print("\nПервые 5 услуг:")
    for s in services[:5]:
        print(f"  [{s.category}] {s.name}: {s.price} руб.")
