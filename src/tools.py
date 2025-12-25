"""
Инструменты для поиска услуг в прайс-листе.
"""

from langchain_core.tools import tool
from rapidfuzz import fuzz, process

from src.config import Service


def create_tools(price_list: list[Service]) -> list:
    """
    Создаёт инструменты для агента с привязкой к прайс-листу.

    Args:
        price_list: Список услуг автосервиса

    Returns:
        Список инструментов для агента
    """

    @tool
    def search_services(query: str) -> str:
        """
        Поиск услуг в прайс-листе автосервиса по ключевым словам.

        Используй этот инструмент когда пользователь спрашивает о:
        - Конкретных услугах (диагностика, замена, ремонт и т.д.)
        - Ценах на услуги
        - Наличии определённых работ

        Args:
            query: Поисковый запрос — используй точные слова из сообщения пользователя,
                   НЕ перефразируй и НЕ заменяй сокращения (ДВС, КПП, ГРМ и т.д.)
                   Примеры: "поддон ДВС", "замена масла", "ремонт КПП"

        Returns:
            Список найденных услуг с ценами или сообщение об отсутствии
        """
        if not price_list:
            return "Ошибка: прайс-лист не загружен"

        # Fuzzy поиск по названию услуги
        results = process.extract(
            query,
            price_list,
            processor=lambda s: s.name if isinstance(s, Service) else s,
            scorer=fuzz.WRatio,
            limit=10,
            score_cutoff=60,
        )

        if not results:
            return f"Услуги по запросу '{query}' не найдены в прайс-листе."

        # Группируем по категориям
        categories: dict[str, list[Service]] = {}
        for service, _score, _idx in results:
            categories.setdefault(service.category, []).append(service)

        # Формируем ответ
        lines = [f"Найдено {len(results)} услуг(и) по запросу '{query}':"]
        for cat, services in sorted(categories.items()):
            lines.append(f"\n{cat}:")
            for s in services:
                lines.append(f"  - {s.name}: {int(s.price)} руб.")

        return "\n".join(lines)

    @tool
    def get_all_categories() -> str:
        """
        Получает список всех категорий услуг автосервиса.

        Используй когда пользователь спрашивает:
        - Какие услуги есть?
        - Что вы предлагаете?
        - Какие категории доступны?
        - Чем занимается автосервис?

        Returns:
            Список категорий с количеством услуг в каждой
        """
        if not price_list:
            return "Ошибка: прайс-лист не загружен"

        # Считаем услуги по категориям
        categories: dict[str, int] = {}
        for s in price_list:
            categories[s.category] = categories.get(s.category, 0) + 1

        lines = ["Доступные категории услуг:\n"]
        for cat, count in sorted(categories.items()):
            lines.append(f"- {cat} ({count})")

        lines.append(
            f"\nВсего: {len(price_list)} услуг в {len(categories)} категориях")
        return "\n".join(lines)

    @tool
    def get_services_by_category(category: str) -> str:
        """
        Получает все услуги конкретной категории с ценами.

        Используй когда пользователь спрашивает об услугах определённой категории:
        - "Услуги по ремонту двигателя"
        - "Что есть по подвеске?"
        - "Покажи все услуги диагностики"
        - "Услуги по тормозам"

        Args:
            category: Название категории или её часть
                      (например: "Двигателя", "подвеск", "тормоз")

        Returns:
            Список услуг категории с ценами
        """
        if not price_list:
            return "Ошибка: прайс-лист не загружен"

        category_lower = category.lower().strip()

        # Ищем категории, содержащие запрос
        matching_categories = set()
        for s in price_list:
            if category_lower in s.category.lower():
                matching_categories.add(s.category)

        if not matching_categories:
            all_cats = sorted(set(s.category for s in price_list))
            return (
                f"Категория '{category}' не найдена.\n\n"
                f"Доступные категории:\n" +
                "\n".join(f"- {c}" for c in all_cats)
            )

        # Собираем услуги
        lines = []
        for cat in sorted(matching_categories):
            services = [s for s in price_list if s.category == cat]
            lines.append(f"\n{cat} ({len(services)} услуг):")
            for s in services:
                lines.append(f"  - {s.name}: {int(s.price)} руб.")

        return "\n".join(lines)

    return [search_services, get_all_categories, get_services_by_category]
