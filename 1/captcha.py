import random
import string
from PIL import Image, ImageDraw, ImageFont
import io
import os


class CaptchaGenerator:
    def __init__(self):
        self.font = None
        self._load_font()

    def _load_font(self):
        """Загрузка шрифта"""
        try:
            # Пробуем разные пути к шрифтам
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                "C:/Windows/Fonts/arial.ttf",  # Windows
                "C:/Windows/Fonts/tahoma.ttf",  # Windows
                "/System/Library/Fonts/Menlo.ttc",  # Mac
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    self.font = ImageFont.truetype(font_path, 36)
                    return

            # Если шрифты не найдены, используем базовый
            self.font = ImageFont.load_default()
            print("⚠️ Системные шрифты не найдены, используется базовый шрифт")

        except Exception as e:
            print(f"❌ Ошибка загрузки шрифта: {e}")
            self.font = ImageFont.load_default()

    def generate_captcha_text(self, length=5):
        """Генерация текста капчи (только цифры для простоты)"""
        return ''.join(random.choice(string.digits) for _ in range(length))

    def create_captcha_image(self, text):
        """Создание изображения капчи"""
        width, height = 200, 80

        # Создаем изображение
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)

        # Добавляем шум - случайные линии
        for _ in range(5):
            x1, y1 = random.randint(0, width), random.randint(0, height)
            x2, y2 = random.randint(0, width), random.randint(0, height)
            draw.line([(x1, y1), (x2, y2)],
                      fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)),
                      width=1)

        # Добавляем шум - случайные точки
        for _ in range(100):
            x, y = random.randint(0, width), random.randint(0, height)
            draw.point((x, y),
                       fill=(random.randint(150, 220), random.randint(150, 220), random.randint(150, 220)))

        # Рисуем текст
        text_width = draw.textlength(text, font=self.font)
        x = (width - text_width) // 2
        y = (height - 36) // 2

        # Добавляем текст с небольшими искажениями
        for i, char in enumerate(text):
            char_x = x + i * (text_width // len(text)) + random.randint(-2, 2)
            char_y = y + random.randint(-3, 3)
            draw.text((char_x, char_y), char,
                      fill=(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)),
                      font=self.font)

        # Сохраняем в байты
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return img_byte_arr

    async def generate_captcha(self):
        """Генерация полной капчи"""
        captcha_text = self.generate_captcha_text()
        captcha_image = self.create_captcha_image(captcha_text)
        return captcha_text, captcha_image


# Глобальный экземпляр
captcha_generator = CaptchaGenerator()
