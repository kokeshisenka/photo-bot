import os
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация бота
BOT_CONFIG = {
    "password": "1337",
    "authorized_users": set(),
    "user_files": {},
    "temp_dir": "temp_files"
}

# Создаем временную директорию
if not os.path.exists(BOT_CONFIG["temp_dir"]):
    os.makedirs(BOT_CONFIG["temp_dir"])

def is_authorized(user_id):
    return user_id in BOT_CONFIG["authorized_users"]

def add_authorized_user(user_id):
    BOT_CONFIG["authorized_users"].add(user_id)
    if user_id not in BOT_CONFIG["user_files"]:
        BOT_CONFIG["user_files"][user_id] = {}

def remove_authorized_user(user_id):
    BOT_CONFIG["authorized_users"].discard(user_id)

def get_user_files(user_id):
    return BOT_CONFIG["user_files"].get(user_id, {})

def set_user_file(user_id, key, file_path):
    if user_id not in BOT_CONFIG["user_files"]:
        BOT_CONFIG["user_files"][user_id] = {}
    BOT_CONFIG["user_files"][user_id][key] = file_path