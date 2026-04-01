# main.py — ВЕРСИЯ С ТЕСТОВЫМИ ФУНКЦИЯМИ
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from maxbot.bot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.types import Message
from yandex_disk import YandexDiskClient
import asyncio

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
    """Обработчик всех сообщений с расширенной отладкой"""
    try:
        # ========== ТЕСТОВАЯ ФУНКЦИЯ 1: ВСЕГДА ЛОГИРУЕМ ВСЕ СООБЩЕНИЯ ==========
        logger.info("=" * 60)
        logger.info(f"🔍 [ТЕСТ] Бот получил сообщение!")
        logger.info(f"🔍 [ТЕСТ] ID чата: {message.chat.id}")
        logger.info(f"🔍 [ТЕСТ] Тип чата: {message.chat.type}")
        logger.info(f"🔍 [ТЕСТ] ID сообщения: {message.id}")
        logger.info(f"🔍 [ТЕСТ] Текст: {message.body.text if message.body else 'Нет текста'}")
        if message.sender:
            logger.info(f"🔍 [ТЕСТ] Отправитель: {message.sender.name} (ID: {message.sender.id})")
        logger.info("=" * 60)
        
        # ========== ТЕСТОВАЯ ФУНКЦИЯ 2: ОТВЕТ НА КОМАНДУ /test ==========
        text = message.body.text if hasattr(message, 'body') and message.body else ""
        if text == "/test":
            await bot.send_message(
                chat_id=message.chat.id,
                text=f"✅ Бот работает! Получено ваше сообщение.\n\n"
                     f"📊 Информация:\n"
                     f"• ID чата: {message.chat.id}\n"
                     f"• Тип чата: {message.chat.type}\n"
                     f"• Ваш ID: {message.sender.id if message.sender else 'Неизвестно'}\n"
                     f"• Ожидаемый канал: {CHANNEL_ID}",
                reply_to_message_id=message.id
            )
            logger.info(f"✅ Отправлен ответ на /test в чат {message.chat.id}")
            return
        
        # Проверяем, что сообщение из нужного канала
        if str(message.chat.id) != CHANNEL_ID:
            logger.info(f"⏭️ Игнорируем (не тот канал). Ожидался: {CHANNEL_ID}, получен: {message.chat.id}")
            return
        
        logger.info(f"✅ Сообщение из целевого канала! Обрабатываем...")
        
        # Проверяем, является ли сообщение ответом (reply)
        if message.reply_to_message:
            await handle_reply(message)
            return
        
        # Обычное сообщение (не ответ)
        await handle_new_message(message)
                
    except Exception as e:
        logger.error(f"❌ Ошибка обработки: {e}", exc_info=True)

async def handle_reply(message: Message):
    """Обработка ответов на сообщения"""
    try:
        reply_text = message.body.text if hasattr(message, 'body') and message.body else ""
        reply_text_lower = reply_text.lower()
        
        is_complete = any(keyword in reply_text_lower for keyword in STATUS_KEYWORDS)
        
        if is_complete:
            original_message_id = message.reply_to_message.id
            logger.info(f"🔄 Обновляем статус сообщения {original_message_id}")
            success = disk.update_status(original_message_id, 'выполнено')
            
            if success:
                logger.info(f"✅ Статус сообщения {original_message_id} обновлен на 'выполнено'")
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f"✅ Статус задачи обновлен на 'выполнено'",
                    reply_to_message_id=original_message_id
                )
            else:
                logger.error(f"❌ Не удалось обновить статус для {original_message_id}")
        else:
            logger.info(f"ℹ️ Ответ не содержит ключевого слова для смены статуса")
                
    except Exception as e:
        logger.error(f"❌ Ошибка обработки reply: {e}", exc_info=True)

async def handle_new_message(message: Message):
    """Обработка нового сообщения (не ответа)"""
    try:
        if disk.check_duplicate(str(message.id)):
            logger.info(f"⏭️ Сообщение {message.id} уже сохранено")
            return
        
        message_data = extract_message_data(message)
        
        if message_data:
            success = disk.append_row(message_data)
            if success:
                logger.info(f"✅ Новое сообщение {message.id} сохранено в Яндекс.Диск")
            else:
                logger.error(f"❌ Ошибка сохранения {message.id}")
                
    except Exception as e:
        logger.error(f"❌ Ошибка обработки нового сообщения: {e}", exc_info=True)

def extract_message_data(message: Message) -> list:
    """Извлечение данных из сообщения MAX"""
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
    """Обработчик запуска бота"""
    logger.info(f"🚀 Бот запущен в чате {event.chat_id}")
    logger.info(f"📋 Ожидаемый канал: {CHANNEL_ID}")

# ========== ТЕСТОВАЯ ФУНКЦИЯ 3: ИНФОРМАЦИЯ О ЗАПУСКЕ ==========
async def test_connection():
    """Тестовая функция для проверки подключения к MAX"""
    try:
        me = await bot.get_me()
        logger.info(f"✅ Подключение к MAX установлено!")
        # API возвращает словарь, поэтому используем .get()
        bot_id = me.get('id') if isinstance(me, dict) else getattr(me, 'id', 'неизвестно')
        bot_name = me.get('name') if isinstance(me, dict) else getattr(me, 'name', 'неизвестно')
        logger.info(f"🤖 Информация о боте: ID: {bot_id}, Имя: {bot_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к MAX: {e}")
        return False

# ========== ТЕСТОВАЯ ФУНКЦИЯ 4: УДАЛЕНИЕ WEBHOOK ==========
async def delete_webhook_if_exists():
    """Удаляем webhook, чтобы использовать polling"""
    try:
        # В некоторых версиях MAX бота может не быть метода delete_webhook
        # Пробуем, если есть
        if hasattr(bot, 'delete_webhook'):
            await bot.delete_webhook()
            logger.info("✅ Webhook удален (если был)")
        else:
            logger.info("ℹ️ Метод delete_webhook не требуется для этой версии")
    except Exception as e:
        logger.info(f"ℹ️ Webhook не требуется: {e}")

# ========== ТЕСТОВАЯ ФУНКЦИЯ 5: ЗАПУСК С ТЕСТАМИ ==========
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🤖 Бот MAX для Яндекс.Диска — ЗАПУСК С ТЕСТАМИ")
    logger.info("=" * 60)
    logger.info(f"📋 Ожидаемый канал: {CHANNEL_ID}")
    logger.info(f"📁 Файл: {disk.file_path}")
    logger.info(f"🔄 Ключевые слова: {STATUS_KEYWORDS}")
    logger.info("=" * 60)
    
    # Запускаем тесты
    loop = asyncio.get_event_loop()
    
    # Тест подключения к MAX
    logger.info("🔍 Проверка подключения к MAX...")
    connection_ok = loop.run_until_complete(test_connection())
    
    if connection_ok:
        logger.info("✅ Бот успешно подключился к MAX")
    else:
        logger.error("❌ Не удалось подключиться к MAX. Проверьте токен!")
    
    # Удаляем webhook
    loop.run_until_complete(delete_webhook_if_exists())
    
    logger.info("=" * 60)
    logger.info("✅ Бот готов к работе! Ожидаем сообщения...")
    logger.info("💡 Для теста напишите в канале: /test")
    logger.info("💡 Если сообщения не приходят, проверьте:")
    logger.info("   1. Бот добавлен в канал как администратор")
    logger.info("   2. У бота есть право 'Чтение сообщений'")
    logger.info("   3. CHANNEL_ID правильный (отрицательное число)")
    logger.info("=" * 60)
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
