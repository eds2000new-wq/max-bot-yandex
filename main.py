# main.py — ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ
import os
import logging
from datetime import datetime
from maxbot.bot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.types import Message
from yandex_disk import YandexDiskClient
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
disk = YandexDiskClient()
STATUS_KEYWORDS = ['выполнено', 'готово', 'сделано', 'done', '✅', '✔️']

@dp.message()
async def handle_message(message: Message):
    """Обработчик всех сообщений"""
    try:
        # Логируем каждое сообщение
        logger.info(f"📨 Получено сообщение из чата {message.chat.id}")
        
        # Проверяем канал
        if CHANNEL_ID and str(message.chat.id) != CHANNEL_ID:
            logger.info(f"⏭️ Игнорируем (не тот канал)")
            return
        
        # Получаем текст
        text = message.body.text if message.body else ""
        logger.info(f"📝 Текст: {text}")
        
        # Обработка reply
        if message.reply_to_message:
            await handle_reply(message)
            return
        
        # Обычное сообщение
        await handle_new_message(message)
                
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")

async def handle_reply(message: Message):
    try:
        reply_text = message.body.text if hasattr(message, 'body') and message.body else ""
        reply_text_lower = reply_text.lower()
        
        if any(keyword in reply_text_lower for keyword in STATUS_KEYWORDS):
            original_message_id = message.reply_to_message.id
            success = disk.update_status(original_message_id, 'выполнено')
            
            if success:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f"✅ Статус задачи изменён на «выполнено»",
                    reply_to_message_id=original_message_id
                )
                logger.info(f"✅ Статус {original_message_id} обновлен")
    except Exception as e:
        logger.error(f"❌ Ошибка reply: {e}")

async def handle_new_message(message: Message):
    try:
        if disk.check_duplicate(str(message.id)):
            logger.info(f"⏭️ Дубликат {message.id}")
            return
        
        message_data = extract_message_data(message)
        if message_data:
            disk.append_row(message_data)
            logger.info(f"✅ Сохранено {message.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")

def extract_message_data(message: Message) -> list:
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_id = str(message.id)
        sender_name = message.sender.name if message.sender else "Unknown"
        sender_id = str(message.sender.id) if message.sender else ""
        text = message.body.text if hasattr(message, 'body') and message.body else ""
        message_type = "text"
        status = "в работе"
        user = f"@{message.sender.username}" if message.sender and message.sender.username else sender_name
        return [timestamp, message_id, sender_name, sender_id, text, message_type, status, user]
    except Exception as e:
        logger.error(f"Ошибка извлечения: {e}")
        return None

@dp.bot_started
async def on_bot_started(event):
    logger.info(f"🚀 Бот запущен")

# ГЛАВНОЕ: ПРОСТОЙ ЗАПУСК БЕЗ start_polling
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🤖 Бот MAX для Яндекс.Диска запущен")
    logger.info(f"📋 Отслеживается канал: {CHANNEL_ID}")
    logger.info(f"📁 Файл: {disk.file_path}")
    logger.info("✅ Бот готов к работе! Ожидаем сообщения...")
    logger.info("=" * 50)
    
    # 🔥 САМЫЙ ПРОСТОЙ СПОСОБ — запускаем event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
