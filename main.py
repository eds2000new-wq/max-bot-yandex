# main.py — с ответами в канале
import os
import logging
from datetime import datetime
from maxbot.bot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.types import Message
from yandex_disk import YandexDiskClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
disk = YandexDiskClient()
STATUS_KEYWORDS = ['выполнено', 'готово', 'сделано', 'done', '✅', '✔️']

@dp.message()
async def handle_message(message: Message):
    try:
        # Проверяем канал
        if str(message.chat.id) != CHANNEL_ID:
            return
        
        # 🆕 ОТВЕТ НА КОМАНДУ /help В КАНАЛЕ
        text = message.body.text if message.body else ""
        if text == "/help":
            await bot.send_message(
                chat_id=message.chat.id,
                text="📖 **Справка**\n\n"
                     "✅ Сообщения автоматически сохраняются в Яндекс.Таблицу\n"
                     "🔄 Ответьте на любое сообщение словом 'выполнено' — статус изменится\n"
                     "📁 Данные: Яндекс.Диск → Приложения/max_bot\n"
                     "❓ Вопросы администратору: @ваш_логин",
                format="markdown",
                reply_to_message_id=message.id
            )
            return
        
        # Обработка reply (изменение статуса)
        if message.reply_to_message:
            await handle_reply(message)
            return
        
        # Обычное сообщение — сохраняем
        await handle_new_message(message)
                
    except Exception as e:
        logger.error(f"❌ Ошибка обработки: {e}")

async def handle_reply(message: Message):
    try:
        reply_text = message.body.text if hasattr(message, 'body') and message.body else ""
        reply_text_lower = reply_text.lower()
        
        if any(keyword in reply_text_lower for keyword in STATUS_KEYWORDS):
            original_message_id = message.reply_to_message.id
            success = disk.update_status(original_message_id, 'выполнено')
            
            if success:
                # 🆕 ПОДТВЕРЖДЕНИЕ В КАНАЛ
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f"✅ Статус задачи изменён на «выполнено»",
                    reply_to_message_id=original_message_id
                )
                logger.info(f"✅ Статус сообщения {original_message_id} обновлен")
    except Exception as e:
        logger.error(f"❌ Ошибка обработки reply: {e}")

async def handle_new_message(message: Message):
    try:
        if disk.check_duplicate(str(message.id)):
            return
        
        message_data = extract_message_data(message)
        if message_data:
            disk.append_row(message_data)
            logger.info(f"✅ Новое сообщение {message.id} сохранено")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")

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
        logger.error(f"Ошибка извлечения данных: {e}")
        return None

@dp.bot_started
async def on_bot_started(event):
    logger.info(f"🚀 Бот запущен")

async def main():
    logger.info("🤖 Бот MAX запущен")
    logger.info(f"📋 Канал: {CHANNEL_ID}")
    
    # Бесконечный цикл для работы бота
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
