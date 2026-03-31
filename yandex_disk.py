# yandex_disk.py — ИСПРАВЛЕННАЯ ВЕРСИЯ
import yadisk
import pandas as pd
from datetime import datetime
import io
import os
from dotenv import load_dotenv

load_dotenv()

class YandexDiskClient:
    def __init__(self):
        """Инициализация клиента Яндекс.Диска"""
        self.token = os.getenv('YANDEX_DISK_TOKEN')
        self.folder = os.getenv('YANDEX_FOLDER', '/Приложения/max_bot')
        self.file_name = 'messages.xlsx'
        self.file_path = f"{self.folder}/{self.file_name}"
        self.client = yadisk.Client(token=self.token)
        
    def ensure_folder_exists(self):
        """Создает папку рекурсивно, если её нет"""
        try:
            with self.client:
                # Проверяем, существует ли папка
                if not self.client.exists(self.folder):
                    # Создаем папку с родительскими директориями
                    self.client.mkdir(self.folder, parent=True)
                    print(f"📁 Создана папка: {self.folder}")
                else:
                    print(f"📁 Папка уже существует: {self.folder}")
        except Exception as e:
            print(f"❌ Ошибка при создании папки: {e}")
    
    def init_table(self):
        """Создает таблицу с заголовками, если её нет"""
        try:
            with self.client:
                # Сначала создаем папку, если её нет
                if not self.client.exists(self.folder):
                    self.client.mkdir(self.folder, parent=True)
                    print(f"📁 Создана папка: {self.folder}")
                
                # Проверяем существование файла
                if not self.client.exists(self.file_path):
                    # Создаем DataFrame с заголовками
                    df = pd.DataFrame(columns=[
                        'timestamp', 'message_id', 'sender_name', 
                        'sender_id', 'text', 'message_type', 
                        'status', 'user'
                    ])
                    
                    # Сохраняем в буфер
                    output = io.BytesIO()
                    df.to_excel(output, index=False, engine='openpyxl')
                    output.seek(0)
                    
                    # Загружаем на Яндекс.Диск
                    self.client.upload(output, self.file_path)
                    print(f"✅ Создан файл: {self.file_path}")
                else:
                    print(f"📁 Файл уже существует: {self.file_path}")
        except Exception as e:
            print(f"❌ Ошибка при создании таблицы: {e}")
    
    def append_row(self, values):
        """Добавление строки в Excel файл"""
        try:
            with self.client:
                # Убеждаемся, что папка и файл существуют
                if not self.client.exists(self.folder):
                    self.client.mkdir(self.folder, parent=True)
                
                if not self.client.exists(self.file_path):
                    self.init_table()
                
                # Скачиваем существующий файл
                buffer = io.BytesIO()
                self.client.download(self.file_path, buffer)
                buffer.seek(0)
                
                # Читаем Excel
                df = pd.read_excel(buffer, engine='openpyxl')
                
                # Добавляем новую строку
                new_row = pd.DataFrame([values], columns=df.columns)
                df = pd.concat([df, new_row], ignore_index=True)
                
                # Сохраняем обратно в буфер
                output = io.BytesIO()
                df.to_excel(output, index=False, engine='openpyxl')
                output.seek(0)
                
                # Загружаем на Яндекс.Диск (с перезаписью)
                self.client.upload(output, self.file_path, overwrite=True)
                
                print(f"✅ Данные сохранены. Всего строк: {len(df)}")
                return True
        except Exception as e:
            print(f"❌ Ошибка при сохранении: {e}")
            return False
    
    def update_status(self, message_id, new_status):
        """Обновление статуса сообщения по ID"""
        try:
            with self.client:
                if not self.client.exists(self.file_path):
                    return False
                    
                buffer = io.BytesIO()
                self.client.download(self.file_path, buffer)
                buffer.seek(0)
                
                df = pd.read_excel(buffer, engine='openpyxl')
                mask = df['message_id'] == str(message_id)
                
                if not mask.any():
                    print(f"❌ Сообщение {message_id} не найдено")
                    return False
                
                df.loc[mask, 'status'] = new_status
                df.loc[mask, 'timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " (обновлено)"
                
                output = io.BytesIO()
                df.to_excel(output, index=False, engine='openpyxl')
                output.seek(0)
                self.client.upload(output, self.file_path, overwrite=True)
                
                print(f"✅ Статус сообщения {message_id} обновлен на '{new_status}'")
                return True
        except Exception as e:
            print(f"❌ Ошибка при обновлении статуса: {e}")
            return False
    
    def check_duplicate(self, message_id):
        """Проверка на дубликат"""
        try:
            with self.client:
                if not self.client.exists(self.file_path):
                    return False
                    
                buffer = io.BytesIO()
                self.client.download(self.file_path, buffer)
                buffer.seek(0)
                df = pd.read_excel(buffer, engine='openpyxl')
                return str(message_id) in df['message_id'].astype(str).values
        except:
            return False
