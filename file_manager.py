import os
import tempfile
from config import BOT_CONFIG, logger

class FileManager:
    def __init__(self):
        self.temp_dir = BOT_CONFIG["temp_dir"]
    
    def create_temp_file(self, suffix=""):
        try:
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=suffix,
                dir=self.temp_dir
            )
            return temp_file.name
        except Exception as e:
            logger.error(f"Ошибка создания временного файла: {e}")
            raise
    
    def save_uploaded_file(self, file_content, suffix=""):
        try:
            temp_path = self.create_temp_file(suffix)
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            return temp_path
        except Exception as e:
            logger.error(f"Ошибка сохранения файла: {e}")
            raise
    
    def cleanup_file(self, file_path):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Ошибка удаления файла: {e}")
    
    def cleanup_user_files(self, user_id):
        user_files = BOT_CONFIG["user_files"].get(user_id, {})
        for file_path in user_files.values():
            if isinstance(file_path, str):
                self.cleanup_file(file_path)
        BOT_CONFIG["user_files"][user_id] = {}

file_manager = FileManager()