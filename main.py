# main.py - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
import os
import logging
from datetime import datetime
from maxbot.bot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.types import Message
from yandex_disk import YandexDiskClient

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Инициализация клиента Яндекс.Диска
disk = YandexDiskClient()

# Ключевые слова для смены статуса
STATUS_KEYWORDS = ['выполнено', 'готово', 'сделано', 'done', '✅', '✔️']

@dp.message()
async def handle_message(message: Message):
    """Обработчик всех сообщений"""
    try:
        # Проверяем канал
        if str(message.chat.id) != CHANNEL_ID:
            return
        
        # Проверяем, ответ ли это
        if message.reply_to_message:
            await handle_reply(message)
            return
        
        # Обычное сообщение
        await handle_new_message(message)
                
    except Exception as e:
        logger.error(f"❌ Ошибка обработки: {e}")

async def handle_reply(message: Message):
    """Обработка ответов"""
    try:
        reply_text = message.body.text if hasattr(message, 'body') and message.body else ""
        reply_text_lower = reply_text.lower()
        
        if any(keyword in reply_text_lower for keyword in STATUS_KEYWORDS):
            original_message_id = message.reply_to_message.id
            success = disk.update_status(original_message_id, 'выполнено')
            
            if success:
                logger.info(f"✅ Статус сообщения {original_message_id} обновлен")
    except Exception as e:
        logger.error(f"❌ Ошибка обработки reply: {e}")

async def handle_new_message(message: Message):
    """Обработка нового сообщения"""
    try:
        if disk.check_duplicate(str(message.id)):
            logger.info(f"⏭️ Сообщение {message.id} уже сохранено")
            return
        
        message_data = extract_message_data(message)
        
        if message_data:
            success = disk.append_row(message_data)
            if success:
                logger.info(f"✅ Новое сообщение {message.id} сохранено")
    except Exception as e:
        logger.error(f"❌ Ошибка обработки нового сообщения: {e}")

def extract_message_data(message: Message) -> list:
    """Извлечение данных из сообщения"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_id = str(message.id)
        sender_name = message.sender.name if message.sender else "Unknown"
        sender_id = str(message.sender.id) if message.sender else ""
        text = message.body.text if hasattr(message, 'body') and message.body else ""
        
        message_type = "text"
        if hasattr(message, 'body') and hasattr(message.body, 'attachments'):
            if message.body.attachments:
                message_type = message.body.attachments[0].type
        
        status = "в работе"
        user = f"@{message.sender.username}" if message.sender and message.sender.username else sender_name
        
        return [timestamp, message_id, sender_name, sender_id, text, message_type, status, user]
        
    except Exception as e:
        logger.error(f"Ошибка извлечения данных: {e}")
        return None

@dp.bot_started
async def on_bot_started(event):
    logger.info(f"🚀 Бот запущен в чате {event.chat_id}")

async def main():
    logger.info("🤖 Бот MAX для Яндекс.Диска запущен")
    logger.info(f"📋 Отслеживается канал: {CHANNEL_ID}")
    logger.info(f"📁 Файл: {disk.file_path}")
    logger.info(f"🔄 Ключевые слова: {STATUS_KEYWORDS}")
    
    # ✅ ПРАВИЛЬНО: polling запускается через бота, а не через диспетчер
    await bot.start_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
