import os
import cv2
import numpy as np
from PIL import Image, ImageFilter
from config import logger

# Проверяем доступность HEIC
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORT = True
    logger.info("✅ HEIC support enabled via pillow-heif")
except ImportError:
    HEIC_SUPPORT = False
    logger.warning("❌ HEIC support disabled")

# Проверяем доступность конвертации В HEIC
try:
    from pillow_heif import register_avif_opener, register_heif_opener
    register_heif_opener()
    register_avif_opener()
    HEIC_WRITE_SUPPORT = True
    logger.info("✅ HEIC write support enabled")
except ImportError:
    HEIC_WRITE_SUPPORT = False
    logger.warning("❌ HEIC write support disabled")

class ImageProcessor:
    
    def convert_image(self, input_path, output_format):
        """Конвертация изображения в другой формат с поддержкой HEIC"""
        try:
            format_extensions = {
                'PNG': '.png',
                'JPEG': '.jpg', 
                'WEBP': '.webp',
                'BMP': '.bmp',
                'HEIC': '.heic'
            }
            
            if output_format not in format_extensions:
                raise ValueError(f"Неподдерживаемый формат: {output_format}")
            
            # Конвертация В HEIC
            if output_format == 'HEIC':
                if not HEIC_WRITE_SUPPORT:
                    raise ImportError("Для конвертации в HEIC установите: pip install pillow-heif")
                
                # Открываем исходное изображение
                image = Image.open(input_path)
                
                # Конвертируем в RGB если нужно (HEIC не поддерживает альфа-канал)
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                
                from file_manager import file_manager
                output_path = file_manager.create_temp_file(suffix='.heic')
                
                # Сохраняем как HEIC
                image.save(output_path, format="HEIC", quality=85)
                return output_path
            
            # Конвертация ИЗ HEIC в другие форматы
            image = Image.open(input_path)
            
            from file_manager import file_manager
            output_path = file_manager.create_temp_file(
                suffix=format_extensions[output_format]
            )
            
            if output_format == 'JPEG':
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                image.save(output_path, 'JPEG', quality=95)
            else:
                image.save(output_path, output_format)
            
            return output_path
                
        except Exception as e:
            logger.error(f"Ошибка конвертации: {e}")
            raise
    
    def test_heic_conversion(self, input_path):
        """Тестирование работы с HEIC файлами"""
        try:
            results = {
                'can_read_heic': False,
                'can_write_heic': False,
                'file_info': {},
                'test_conversion': False
            }
            
            # Проверяем чтение HEIC
            if input_path.lower().endswith(('.heic', '.heif')):
                if not HEIC_SUPPORT:
                    raise Exception("HEIC чтение недоступно")
                
                image = Image.open(input_path)
                results['can_read_heic'] = True
                results['file_info'] = {
                    'format': 'HEIC',
                    'size': image.size,
                    'mode': image.mode
                }
                
                # Пробуем конвертировать HEIC в PNG
                from file_manager import file_manager
                test_output = file_manager.create_temp_file(suffix='_test.png')
                if image.mode == 'RGBA':
                    image.save(test_output, 'PNG')
                else:
                    image.save(test_output, 'PNG')
                
                if os.path.exists(test_output):
                    results['test_conversion'] = True
                    os.remove(test_output)  # Очищаем тестовый файл
            
            # Проверяем запись HEIC
            if HEIC_WRITE_SUPPORT:
                results['can_write_heic'] = True
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка тестирования HEIC: {e}")
            return results
    
    def upscale_2x_advanced(self, input_path):
        """Продвинутое увеличение с использованием OpenCV"""
        try:
            # Чтение изображения
            img = cv2.imread(input_path)
            if img is None:
                raise ValueError("Невозможно прочитать изображение")
            
            # Получаем текущие размеры
            height, width = img.shape[:2]
            
            # Увеличиваем в 2 раза с лучшей интерполяцией
            new_size = (width * 2, height * 2)
            upscaled_img = cv2.resize(img, new_size, interpolation=cv2.INTER_LANCZOS4)
            
            # Улучшение резкости
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            upscaled_img = cv2.filter2D(upscaled_img, -1, kernel)
            
            from file_manager import file_manager
            output_path = file_manager.create_temp_file(suffix='_2x_advanced.png')
            cv2.imwrite(output_path, upscaled_img)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка продвинутого upscale: {e}")
            raise
    
    def upscale_2x_simple(self, input_path):
        """Простое увеличение разрешения в 2 раза"""
        try:
            with Image.open(input_path) as img:
                width, height = img.size
                new_size = (width * 2, height * 2)
                
                # Используем LANCZOS для лучшего качества
                upscaled_img = img.resize(new_size, Image.LANCZOS)
                
                # Легкое повышение резкости
                upscaled_img = upscaled_img.filter(ImageFilter.SHARPEN)
                
                from file_manager import file_manager
                output_path = file_manager.create_temp_file(suffix='_2x_simple.png')
                upscaled_img.save(output_path, 'PNG')
                
                return output_path
                
        except Exception as e:
            logger.error(f"Ошибка простого upscale: {e}")
            raise
    
    def upscale_2x_enhanced(self, input_path):
        """Улучшенное увеличение с комбинированным подходом"""
        try:
            # Сначала используем OpenCV для увеличения
            img = cv2.imread(input_path)
            if img is None:
                raise ValueError("Невозможно прочитать изображение")
            
            height, width = img.shape[:2]
            new_size = (width * 2, height * 2)
            
            # Увеличиваем с помощью OpenCV
            upscaled_cv = cv2.resize(img, new_size, interpolation=cv2.INTER_LANCZOS4)
            
            # Конвертируем в PIL для дополнительной обработки
            upscaled_rgb = cv2.cvtColor(upscaled_cv, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(upscaled_rgb)
            
            # Применяем легкое шумоподавление и резкость
            pil_img = pil_img.filter(ImageFilter.SMOOTH)
            pil_img = pil_img.filter(ImageFilter.SHARPEN)
            
            from file_manager import file_manager
            output_path = file_manager.create_temp_file(suffix='_2x_enhanced.png')
            pil_img.save(output_path, 'PNG', optimize=True)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка улучшенного upscale: {e}")
            raise
    
    def get_image_info(self, image_path):
        """Получение информации об изображении"""
        try:
            image = Image.open(image_path)
            return {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации: {e}")
            return {}

image_processor = ImageProcessor()