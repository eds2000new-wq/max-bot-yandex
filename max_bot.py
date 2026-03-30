# max_bot.py
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from maxbot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.types import Message
from yandex_disk import YandexDiskClient

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('MAX_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Инициализация клиента Яндекс.Диска
disk = YandexDiskClient()

# При запуске проверяем папку и таблицу
disk.ensure_folder_exists()
disk.init_table()

# Ключевые слова для изменения статуса
STATUS_KEYWORDS = ['выполнено', 'готово', 'сделано', 'done', '✅', '✔️']

@dp.message()
async def handle_message(message: Message):
print(f"🔥 ID канала: {message.chat.id}")
    """Обработчик всех сообщений"""
    try:
        # Проверяем, что сообщение из нужного канала
        if str(message.chat.id) != CHANNEL_ID:
            return
        
        # Получаем текст сообщения
        text = message.body.text if hasattr(message, 'body') and message.body else ""
        
        # Проверяем, является ли сообщение ответом (reply)
        if message.reply_to_message:
            await handle_reply(message)
            return
        
        # Обычное сообщение (не ответ)
        await handle_new_message(message)
                
    except Exception as e:
        logger.error(f"❌ Ошибка обработки: {e}")

async def handle_reply(message: Message):
    """Обработка ответов на сообщения"""
    try:
        # Получаем текст ответа
        reply_text = message.body.text if hasattr(message, 'body') and message.body else ""
        reply_text_lower = reply_text.lower()
        
        # Проверяем, содержит ли ответ ключевое слово
        is_complete = any(keyword in reply_text_lower for keyword in STATUS_KEYWORDS)
        
        if is_complete:
            # Получаем ID исходного сообщения (на которое ответили)
            original_message_id = message.reply_to_message.id
            
            # Обновляем статус в таблице
            success = disk.update_status(original_message_id, 'выполнено')
            
            if success:
                logger.info(f"✅ Статус сообщения {original_message_id} обновлен на 'выполнено'")
                
                # Отправляем подтверждение в канал (опционально)
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f"✅ Статус задачи обновлен на 'выполнено'"
                )
            else:
                logger.error(f"❌ Не удалось обновить статус для {original_message_id}")
                
    except Exception as e:
        logger.error(f"❌ Ошибка обработки reply: {e}")

async def handle_new_message(message: Message):
    """Обработка нового сообщения (не ответа)"""
    try:
        # Проверка на дубликат
        if disk.check_duplicate(str(message.id)):
            logger.info(f"⏭️ Сообщение {message.id} уже сохранено")
            return
        
        # Извлечение данных
        message_data = extract_message_data(message)
        
        # Сохранение в Яндекс.Диск
        if message_data:
            success = disk.append_row(message_data)
            if success:
                logger.info(f"✅ Новое сообщение {message.id} сохранено")
            else:
                logger.error(f"❌ Ошибка сохранения {message.id}")
                
    except Exception as e:
        logger.error(f"❌ Ошибка обработки нового сообщения: {e}")

def extract_message_data(message: Message) -> list:
    """Извлечение данных из сообщения MAX"""
    try:
        # Время
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ID сообщения
        message_id = str(message.id)
        
        # Информация об отправителе
        sender_name = message.sender.name if message.sender else "Unknown"
        sender_id = str(message.sender.id) if message.sender else ""
        
        # Текст сообщения
        text = message.body.text if hasattr(message, 'body') and message.body else ""
        
        # Тип сообщения
        message_type = "text"
        if hasattr(message, 'body') and hasattr(message.body, 'attachments'):
            if message.body.attachments:
                message_type = message.body.attachments[0].type
        
        # СТАТУС: по умолчанию "в работе"
        status = "в работе"
        
        # ПОЛЬЗОВАТЕЛЬ: кто написал (username или имя)
        user = f"@{message.sender.username}" if message.sender and message.sender.username else sender_name
        
        return [timestamp, message_id, sender_name, sender_id, text, message_type, status, user]
        
    except Exception as e:
        logger.error(f"Ошибка извлечения данных: {e}")
        return None

@dp.bot_started()
async def on_bot_started(event):
    """Обработчик запуска бота"""
    logger.info(f"🚀 Бот MAX для Яндекс.Диска запущен")
    logger.info(f"📋 Отслеживается канал: {CHANNEL_ID}")

async def main():
    """Запуск бота"""
    logger.info("🤖 Бот MAX запущен и слушает сообщения...")
    logger.info(f"📋 Канал: {CHANNEL_ID}")
    logger.info(f"📁 Файл: {disk.file_path}")
    logger.info(f"🔄 Ключевые слова для статуса: {STATUS_KEYWORDS}")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
