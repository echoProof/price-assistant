"""
Telegram бот для ассистента автосервиса.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AutoServiceBot:
    """Telegram бот для ассистента автосервиса."""

    def __init__(self, token: str, db_path: str = "data/telegram_checkpoints.db"):
        """
        Инициализация бота.

        Args:
            token: Telegram Bot API token
            db_path: Путь к SQLite базе для хранения состояния
        """
        self.token = token
        self.db_path = db_path
        self.agent = None
        self.checkpointer = None
        self.tools = None

    def _init_agent(self):
        """Инициализирует агента с persistence."""
        from src.config import get_llm
        from src.data_loader import load_price_list
        from src.tools import create_tools
        from src.agent import build_agent

        logger.info("Инициализация агента для Telegram бота...")

        # Загружаем прайс-лист
        price_list = load_price_list()
        logger.info(f"Загружено {len(price_list)} услуг")

        # Создаём инструменты и LLM
        self.tools = create_tools(price_list)
        llm = get_llm()

        # Создаём директорию для базы данных
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Создаём checkpointer
        import sqlite3
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.checkpointer = SqliteSaver(conn)

        # Создаём агент с persistence
        self.agent = build_agent(
            self.tools, llm, checkpointer=self.checkpointer)
        logger.info("Агент инициализирован")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start."""
        welcome_message = (
            "Привет! Я ассистент автосервиса.\n\n"
            "Я могу ответить на вопросы о наших услугах и ценах.\n\n"
            "Примеры вопросов:\n"
            "- Какие услуги у вас есть?\n"
            "- Сколько стоит диагностика двигателя?\n"
            "- Что по ремонту подвески?\n\n"
            "Задайте ваш вопрос!"
        )
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help."""
        help_message = (
            "Я могу помочь с информацией об услугах автосервиса.\n\n"
            "Доступные команды:\n"
            "/start - Начать диалог\n"
            "/help - Показать эту справку\n"
            "/categories - Показать все категории услуг\n"
            "/reset - Очистить историю диалога\n\n"
            "Или просто напишите ваш вопрос!"
        )
        await update.message.reply_text(help_message)

    async def categories_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /categories."""
        # get_all_categories - второй инструмент в списке
        get_all_categories = self.tools[1]
        result = get_all_categories.invoke({})
        await update.message.reply_text(result)

    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /reset - очистка истории диалога."""
        chat_id = update.effective_chat.id
        thread_id = f"telegram-{chat_id}"

        try:
            # Удаляем checkpoints и writes для данного thread_id
            with self.checkpointer.cursor() as cur:
                cur.execute(
                    "DELETE FROM checkpoints WHERE thread_id = ?",
                    (thread_id,)
                )
                cur.execute(
                    "DELETE FROM writes WHERE thread_id = ?",
                    (thread_id,)
                )

            logger.info(f"[{chat_id}] История диалога очищена")
            await update.message.reply_text(
                "История диалога очищена. Можем начать сначала!"
            )
        except Exception as e:
            logger.error(f"Ошибка очистки истории: {e}", exc_info=True)
            await update.message.reply_text(
                "Не удалось очистить историю. Попробуйте позже."
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений."""
        user_message = update.message.text
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name or "Пользователь"

        logger.info(f"[{chat_id}] {user_name}: {user_message}")

        # Используем chat_id как thread_id для persistence
        config = {"configurable": {"thread_id": f"telegram-{chat_id}"}}

        try:
            # Показываем индикатор набора текста
            await update.message.chat.send_action("typing")

            # Вызываем агента
            result = self.agent.invoke(
                {"messages": [HumanMessage(content=user_message)]},
                config=config
            )

            # Получаем ответ
            response = result["messages"][-1].content
            logger.info(f"[{chat_id}] Бот: {response[:100]}...")

            # Отправляем ответ (разбиваем на части если слишком длинный)
            max_length = 4000
            if len(response) > max_length:
                for i in range(0, len(response), max_length):
                    await update.message.reply_text(response[i:i + max_length])
            else:
                await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}", exc_info=True)
            await update.message.reply_text(
                "Извините, произошла ошибка при обработке вашего запроса. "
                "Попробуйте ещё раз или переформулируйте вопрос."
            )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок."""
        logger.error(f"Ошибка: {context.error}", exc_info=context.error)

    def run(self):
        """Запускает бота."""
        # Инициализируем агента
        self._init_agent()

        # Создаём приложение
        app = Application.builder().token(self.token).build()

        # Регистрируем обработчики
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("categories", self.categories_command))
        app.add_handler(CommandHandler("reset", self.reset_command))
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.add_error_handler(self.error_handler)

        # Запускаем бота
        logger.info("Запуск Telegram бота...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Entry point для запуска бота."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Ошибка: TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        print("\nДобавьте в .env файл:")
        print("TELEGRAM_BOT_TOKEN=ваш-токен-от-BotFather")
        return

    bot = AutoServiceBot(token)
    bot.run()


if __name__ == "__main__":
    main()
