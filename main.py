# main.py - ИСПРАВЛЕННАЯ И УПРОЩЕННАЯ ВЕРСИЯ
import asyncio
import logging
from maxbot.bot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.types import Message

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- ИНИЦИАЛИЗАЦИЯ ---
# 1. Токен бота подхватится автоматически из переменной окружения BOT_TOKEN на Bothost
bot = Bot()
dp = Dispatcher(bot)

# --- ОБРАБОТЧИК СООБЩЕНИЙ ---
@dp.message()
async def handle_message(message: Message):
    # Здесь будет ваша основная логика
    logging.info(f"Получено сообщение: {message.body.text if message.body else ''}")
    # ВАЖНО: Пока просто выводим в лог, что бот работает.
    # Позже вы сможете добавить сюда код для сохранения в Яндекс.Диск.

# --- ЗАПУСК БОТА ---
# Этот блок является правильной и единственно необходимой точкой входа
async def main():
    # Сам бот уже готов к работе.
    # Нам нужно лишь удерживать программу запущенной.
    # Библиотека не требует дополнительных методов вроде start_polling.
    logging.info("Бот запущен и ожидает сообщения...")
    # Бесконечный цикл, чтобы бот не завершил работу
    while True:
        await asyncio.sleep(3600)  # Пауза, чтобы не нагружать процессор

if __name__ == "__main__":
    asyncio.run(main())
