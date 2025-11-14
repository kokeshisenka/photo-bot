import os
import time
import sys
import telebot
from telebot import types
from config import *
from file_manager import file_manager
from image_processor import image_processor, HEIC_SUPPORT, HEIC_WRITE_SUPPORT

# Инициализация бота
try:
    bot = telebot.TeleBot("8405746152:AAFpKP1sZuZ_TDjoJ6D6gu86PShu4zuWDNg")  # ЗАМЕНИТЕ НА ВАШ ТОКЕН
    logger.info("🤖 Бот инициализирован")
except Exception as e:
    logger.error(f"❌ Ошибка инициализации бота: {e}")
    exit(1)

# Красивые эмодзи и стили
class Styles:
    BLUE = "🔵"
    GREEN = "🟢"
    RED = "🔴"
    YELLOW = "🟡"
    PURPLE = "🟣"
    ORANGE = "🟠"
    
    CONVERT = "🔄"
    UPSCALE = "🚀"
    SETTINGS = "⚙️"
    INFO = "ℹ️"
    WARNING = "⚠️"
    SUCCESS = "✅"
    ERROR = "❌"
    PHOTO = "📸"
    FOLDER = "📁"
    LOCK = "🔒"
    UNLOCK = "🔓"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    welcome_text = f"""
{Styles.PURPLE} *Вітаю, {user_name}!* {Styles.PURPLE}

🤖 *Фото-Майстер Бот* - ваш помічник у роботі з зображеннями

{Styles.GREEN}✨ Доступні функції:

{Styles.CONVERT} *Конвертація форматів*
  ↳ HEIC, PNG, JPEG, WEBP, BMP

{Styles.UPSCALE} *Збільшення якості*  
  ↳ 3 методи покращення

{Styles.SETTINGS} *Управління файлами*
  ↳ Безпечне зберігання

{Styles.LOCK} *Захист паролем*
  ↳ Ваші фото в безпеці

📋 *Використовуйте меню нижче або команди:*
"""
    
    if is_authorized(user_id):
        markup = create_main_menu()
        bot.send_message(message.chat.id, welcome_text, 
                        parse_mode='Markdown', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, welcome_text + 
                        f"\n{Styles.LOCK} *Для доступу введіть:*\n`/auth <пароль>`", 
                        parse_mode='Markdown')

@bot.message_handler(commands=['auth'])
def handle_auth(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if is_authorized(user_id):
        bot.send_message(message.chat.id, 
                        f"{Styles.SUCCESS} *Ви вже авторизовані, {user_name}!*", 
                        parse_mode='Markdown')
        show_main_menu(message)
        return
    
    try:
        password = message.text.split()[1]
        if password == BOT_CONFIG["password"]:
            add_authorized_user(user_id)
            
            success_text = f"""
{Styles.SUCCESS} *Авторизація успішна!*

👋 *Ласкаво просимо, {user_name}!*

✨ Тепер вам доступні всі функції бота:
• Конвертація форматів
• Збільшення якості  
• Безпечне зберігання

📋 *Оберіть дію з меню:*
"""
            markup = create_main_menu()
            bot.send_message(message.chat.id, success_text, 
                           parse_mode='Markdown', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, 
                           f"{Styles.ERROR} *Невірний пароль!*", 
                           parse_mode='Markdown')
    except IndexError:
        bot.send_message(message.chat.id, 
                        f"{Styles.WARNING} *Використання:* `/auth <пароль>`", 
                        parse_mode='Markdown')

@bot.message_handler(commands=['logout'])
def handle_logout(message):
    user_id = message.from_user.id
    
    if is_authorized(user_id):
        file_manager.cleanup_user_files(user_id)
        remove_authorized_user(user_id)
        bot.send_message(message.chat.id, 
                        f"{Styles.SUCCESS} *Ви вийшли з системи*\n\n"
                        f"{Styles.LOCK} *Для повторного входу використовуйте:*\n`/auth <пароль>`", 
                        parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, 
                        f"{Styles.ERROR} *Ви не авторизовані*", 
                        parse_mode='Markdown')

@bot.message_handler(commands=['convert'])
def handle_convert(message):
    user_id = message.from_user.id
    
    if not is_authorized(user_id):
        ask_for_auth(message)
        return
    
    formats_info = ""
    if HEIC_SUPPORT:
        formats_info += f"{Styles.GREEN} • Читання HEIC\n"
    if HEIC_WRITE_SUPPORT:
        formats_info += f"{Styles.GREEN} • Запис HEIC\n"
    
    convert_text = f"""
{Styles.CONVERT} *КОНВЕРТАЦІЯ ФОТО*

{Styles.PHOTO} *Підтримувані формати:*
{formats_info}
{Styles.BLUE} • PNG, JPEG, WEBP, BMP

📤 *Надішліть фото для конвертації:*
"""
    
    bot.send_message(message.chat.id, convert_text, parse_mode='Markdown')
    bot.register_next_step_handler(message, process_convert_image)

def process_convert_image(message):
    user_id = message.from_user.id
    
    if not is_authorized(user_id):
        ask_for_auth(message)
        return
    
    if message.content_type != 'photo' and message.document is None:
        bot.send_message(message.chat.id, 
                        f"{Styles.ERROR} *Будь ласка, надішліть фото або файл!*", 
                        parse_mode='Markdown')
        return
    
    try:
        if message.content_type == 'photo':
            file_info = bot.get_file(message.photo[-1].file_id)
        else:
            file_info = bot.get_file(message.document.file_id)
        
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Определяем расширение
        file_ext = '.jpg'
        if message.document and message.document.file_name:
            filename = message.document.file_name.lower()
            if filename.endswith('.heic') or filename.endswith('.heif'):
                file_ext = '.heic'
            elif filename.endswith('.png'):
                file_ext = '.png'
            elif filename.endswith('.webp'):
                file_ext = '.webp'
            elif filename.endswith('.bmp'):
                file_ext = '.bmp'
        
        input_path = file_manager.save_uploaded_file(downloaded_file, file_ext)
        set_user_file(user_id, 'convert_input', input_path)
        
        # Создаем красивую клавиатуру выбора форматов
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
        
        formats = [
            f"{Styles.BLUE} PNG", 
            f"{Styles.GREEN} JPEG", 
            f"{Styles.ORANGE} WEBP", 
            f"{Styles.PURPLE} BMP"
        ]
        if HEIC_WRITE_SUPPORT:
            formats.append(f"{Styles.YELLOW} HEIC")
        
        for fmt in formats:
            markup.add(fmt)
        
        original_info = image_processor.get_image_info(input_path)
        
        bot.send_message(message.chat.id, 
                        f"{Styles.SUCCESS} *Фото отримано!*\n\n"
                        f"📊 *Інформація:*\n"
                        f"• Формат: `{original_info['format']}`\n"
                        f"• Розмір: `{original_info['width']}x{original_info['height']}`\n\n"
                        f"{Styles.CONVERT} *Оберіть цільовий формат:*", 
                        parse_mode='Markdown', 
                        reply_markup=markup)
        
        bot.register_next_step_handler(message, process_convert_format)
        
    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        bot.send_message(message.chat.id, 
                        f"{Styles.ERROR} *Помилка обробки файлу*", 
                        parse_mode='Markdown')

def process_convert_format(message):
    user_id = message.from_user.id
    
    if not is_authorized(user_id):
        ask_for_auth(message)
        return
    
    # Извлекаем чистый формат из текста с эмодзи
    format_text = message.text.strip()
    format_choice = format_text.split()[-1].upper() if ' ' in format_text else format_text.upper()
    
    valid_formats = ['PNG', 'JPEG', 'WEBP', 'BMP']
    if HEIC_WRITE_SUPPORT:
        valid_formats.append('HEIC')
    
    if format_choice not in valid_formats:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 
                        f"{Styles.ERROR} *Невірний формат!*", 
                        parse_mode='Markdown', 
                        reply_markup=markup)
        return
    
    try:
        user_files = get_user_files(user_id)
        input_path = user_files.get('convert_input')
        
        if not input_path:
            markup = types.ReplyKeyboardRemove()
            bot.send_message(message.chat.id, 
                            f"{Styles.ERROR} *Файл не знайдено*", 
                            parse_mode='Markdown', 
                            reply_markup=markup)
            return
        
        original_info = image_processor.get_image_info(input_path)
        
        processing_msg = bot.send_message(message.chat.id, 
                                        f"{Styles.CONVERT} *Конвертую в {format_choice}...*", 
                                        parse_mode='Markdown')
        
        output_path = image_processor.convert_image(input_path, format_choice)
        
        with open(output_path, 'rb') as result_file:
            file_size = os.path.getsize(output_path) / 1024
            
            success_text = f"""
{Styles.SUCCESS} *Конвертація завершена!*

📊 *Результат:*
• Формат: `{format_choice}`
• Розмір: `{original_info['width']}x{original_info['height']}`
• Вага: `{file_size:.1f} KB`

💾 *Файл готовий до використання*
"""
            
            if format_choice in ['PNG', 'JPEG', 'WEBP']:
                bot.send_photo(message.chat.id, result_file, caption=success_text, parse_mode='Markdown')
            else:
                bot.send_document(message.chat.id, result_file, caption=success_text, parse_mode='Markdown')
        
        set_user_file(user_id, f'converted_{format_choice}', output_path)
        
        bot.delete_message(message.chat.id, processing_msg.message_id)
        markup = types.ReplyKeyboardRemove()
        show_main_menu(message)
        
    except ImportError as e:
        bot.send_message(message.chat.id, 
                        f"{Styles.ERROR} *Помилка:* {str(e)}", 
                        parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Ошибка конвертации: {e}")
        bot.send_message(message.chat.id, 
                        f"{Styles.ERROR} *Помилка конвертації:* {str(e)}", 
                        parse_mode='Markdown')

@bot.message_handler(commands=['upscale'])
def handle_upscale(message):
    user_id = message.from_user.id
    
    if not is_authorized(user_id):
        ask_for_auth(message)
        return
    
    upscale_text = f"""
{Styles.UPSCALE} *ПОКРАЩЕННЯ ЯКОСТІ*

🔍 *Збільшення роздільної здатності 2x*

🎯 *Доступні методи:*

{Styles.GREEN}🚀 *Покращений* 
  ↳ Найкраща якість (повільно)

{Styles.BLUE}⚡ *Розширений*
  ↳ Баланс якості/швидкості

{Styles.ORANGE}📱 *Простий*
  ↳ Швидке покращення

📤 *Надішліть фото для обробки:*
"""
    
    bot.send_message(message.chat.id, upscale_text, parse_mode='Markdown')
    bot.register_next_step_handler(message, process_upscale_image_first)

def process_upscale_image_first(message):
    user_id = message.from_user.id
    
    if not is_authorized(user_id):
        ask_for_auth(message)
        return
    
    if message.content_type != 'photo' and message.document is None:
        bot.send_message(message.chat.id, 
                        f"{Styles.ERROR} *Будь ласка, надішліть фото або файл!*", 
                        parse_mode='Markdown')
        return
    
    try:
        if message.content_type == 'photo':
            file_info = bot.get_file(message.photo[-1].file_id)
        else:
            file_info = bot.get_file(message.document.file_id)
        
        downloaded_file = bot.download_file(file_info.file_path)
        input_path = file_manager.save_uploaded_file(downloaded_file, '.png')
        set_user_file(user_id, 'upscale_input', input_path)
        
        original_info = image_processor.get_image_info(input_path)
        
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=1)
        markup.add(
            f"{Styles.GREEN}🚀 Покращений (OpenCV+PIL)",
            f"{Styles.BLUE}⚡ Розширений (OpenCV)", 
            f"{Styles.ORANGE}📱 Простий (PIL)"
        )
        
        bot.send_message(message.chat.id,
                        f"{Styles.SUCCESS} *Фото отримано!*\n\n"
                        f"📊 *Початкові параметри:*\n"
                        f"• Розмір: `{original_info['width']}x{original_info['height']}`\n\n"
                        f"{Styles.UPSCALE} *Оберіть метод обробки:*", 
                        parse_mode='Markdown', 
                        reply_markup=markup)
        
        bot.register_next_step_handler(message, process_upscale_method_after_image)
        
    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        bot.send_message(message.chat.id, 
                        f"{Styles.ERROR} *Помилка обробки файлу*", 
                        parse_mode='Markdown')

def process_upscale_method_after_image(message):
    user_id = message.from_user.id
    
    if not is_authorized(user_id):
        ask_for_auth(message)
        return
    
    method_choice = message.text
    valid_methods = [
        f"{Styles.GREEN}🚀 Покращений (OpenCV+PIL)",
        f"{Styles.BLUE}⚡ Розширений (OpenCV)", 
        f"{Styles.ORANGE}📱 Простий (PIL)"
    ]
    
    if method_choice not in valid_methods:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 
                        f"{Styles.ERROR} *Невірний метод!*", 
                        parse_mode='Markdown', 
                        reply_markup=markup)
        return
    
    try:
        user_files = get_user_files(user_id)
        input_path = user_files.get('upscale_input')
        
        if not input_path:
            markup = types.ReplyKeyboardRemove()
            bot.send_message(message.chat.id, 
                            f"{Styles.ERROR} *Файл не знайдено*", 
                            parse_mode='Markdown', 
                            reply_markup=markup)
            return
        
        processing_msg = bot.send_message(message.chat.id, 
                                        f"{Styles.UPSCALE} *Обробка...*", 
                                        parse_mode='Markdown')
        
        original_info = image_processor.get_image_info(input_path)
        
        # Выбираем метод upscale
        if "Покращений" in method_choice:
            output_path = image_processor.upscale_2x_enhanced(input_path)
            method_name = "🚀 Покращений"
        elif "Розширений" in method_choice:
            output_path = image_processor.upscale_2x_advanced(input_path)
            method_name = "⚡ Розширений"
        else:
            output_path = image_processor.upscale_2x_simple(input_path)
            method_name = "📱 Простий"
        
        new_info = image_processor.get_image_info(output_path)
        file_size = os.path.getsize(output_path) / 1024
        
        result_text = f"""
{Styles.SUCCESS} *Якість покращена!*

📊 *Результат обробки:*
• Метод: {method_name}
• Розмір: `{original_info['width']}x{original_info['height']}` → `{new_info['width']}x{new_info['height']}`
• Вага: `{file_size:.1f} KB`

✨ *Зображення готове!*
"""
        
        with open(output_path, 'rb') as result_file:
            bot.send_photo(message.chat.id, result_file, caption=result_text, parse_mode='Markdown')
        
        set_user_file(user_id, 'upscaled', output_path)
        
        bot.delete_message(message.chat.id, processing_msg.message_id)
        markup = types.ReplyKeyboardRemove()
        show_main_menu(message)
        
    except Exception as e:
        logger.error(f"Ошибка upscale: {e}")
        bot.send_message(message.chat.id, 
                        f"{Styles.ERROR} *Помилка покращення якості:* {str(e)}", 
                        parse_mode='Markdown')

@bot.message_handler(commands=['cleanup'])
def handle_cleanup(message):
    user_id = message.from_user.id
    
    if not is_authorized(user_id):
        ask_for_auth(message)
        return
    
    file_manager.cleanup_user_files(user_id)
    bot.send_message(message.chat.id, 
                    f"{Styles.SUCCESS} *Всі тимчасові файли очищено!*\n\n"
                    f"{Styles.FOLDER} *Сховище повністю вільне*", 
                    parse_mode='Markdown')

@bot.message_handler(commands=['help', 'menu'])
def handle_help(message):
    show_main_menu(message)

@bot.message_handler(func=lambda message: message.text and '🔄 конвертувати' in message.text.lower())
def handle_convert_button(message):
    handle_convert(message)

@bot.message_handler(func=lambda message: message.text and '🚀 покращити' in message.text.lower())
def handle_upscale_button(message):
    handle_upscale(message)

@bot.message_handler(func=lambda message: message.text and '📁 очистити' in message.text.lower())
def handle_cleanup_button(message):
    handle_cleanup(message)

@bot.message_handler(func=lambda message: message.text and 'ℹ️ допомога' in message.text.lower())
def handle_help_button(message):
    handle_help(message)

@bot.message_handler(func=lambda message: message.text and '🔓 вийти' in message.text.lower())
def handle_logout_button(message):
    handle_logout(message)

def create_main_menu():
    """Создает красивое главное меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    buttons = [
        f"{Styles.CONVERT} Конвертувати",
        f"{Styles.UPSCALE} Покращити", 
        f"{Styles.FOLDER} Очистити",
        f"{Styles.INFO} Допомога",
        f"{Styles.LOCK} Вийти"
    ]
    
    # Распределяем кнопки по 2 в ряд
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i + 1])
        else:
            markup.row(buttons[i])
    
    return markup

def show_main_menu(message):
    """Показывает главное меню"""
    heic_status = f"{Styles.GREEN}Увімкнено" if HEIC_SUPPORT else f"{Styles.RED}Вимкнено"
    heic_write_status = f"{Styles.GREEN}Увімкнено" if HEIC_WRITE_SUPPORT else f"{Styles.RED}Вимкнено"
    
    menu_text = f"""
{Styles.PURPLE} *ГОЛОВНЕ МЕНЮ* {Styles.PURPLE}

{Styles.CONVERT} *Конвертація форматів*
  ↳ HEIC: {heic_status}
  ↳ Запис HEIC: {heic_write_status}

{Styles.UPSCALE} *Покращення якості*
  ↳ 3 методи збільшення

{Styles.FOLDER} *Управління файлами*
  ↳ Безпечне сховище

📋 *Оберіть дію з меню нижче:*
"""
    
    markup = create_main_menu()
    bot.send_message(message.chat.id, menu_text, parse_mode='Markdown', reply_markup=markup)

def ask_for_auth(message):
    """Запрос авторизации"""
    bot.send_message(message.chat.id, 
                    f"{Styles.LOCK} *Доступ заборонено*\n\n"
                    f"Для доступу до бота введіть пароль:\n"
                    f"`/auth <пароль>`", 
                    parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    if not is_authorized(message.from_user.id):
        ask_for_auth(message)
    else:
        bot.send_message(message.chat.id, 
                        f"{Styles.WARNING} *Невідома команда*\n\n"
                        f"Використовуйте меню або команду /help", 
                        parse_mode='Markdown')

if __name__ == "__main__":
    logger.info("🤖 Бот запускается...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"❌ Ошибка в работе бота: {e}")

        
if __name__ == "__main__":
    logger.info("🤖 Бот запускається...")
    
    # Обробка перезапусків
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Бот впав з помилкою: {e}")
            logger.info("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)