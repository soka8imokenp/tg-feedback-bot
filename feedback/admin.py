import os
import requests
from django.contrib import admin
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    # Поля, которые видны в списке
    list_display = ('username', 'category', 'created_at', 'is_answered')
    list_filter = ('category',)
    
    # Метод для отображения галочки "Отвечено" в списке
    def is_answered(self, obj):
        return bool(obj.answer)
    is_answered.boolean = True
    is_answered.short_description = "Javob berildi"

    def save_model(self, request, obj, form, change):
        # 1. Сначала сохраняем данные в базу
        super().save_model(request, obj, form, change)

        # 2. Если поле ответа заполнено, отправляем в Telegram
        if obj.answer:
            bot_token = os.getenv("BOT_TOKEN")
            user_id = obj.user_id
            
            text = (
                f"<b>📩 Sizning murojaatingizga javob keldi!</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"<b>Sizning xabaringiz:</b>\n<i>{obj.text}</i>\n\n"
                f"<b>Admin javobi:</b>\n✅ {obj.answer}\n"
                f"━━━━━━━━━━━━━━\n"
                f"Rahmat, biz bilan qolganingiz uchun!"
            )
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            try:
                payload = {
                    "chat_id": user_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, data=payload)
                if response.status_code == 200:
                    self.message_user(request, f"Javob @{obj.username} ga muvaffaqiyatli yuborildi.")
                else:
                    self.message_user(request, f"Xatolik: Telegramga yuborib bo'lmadi.", level='error')
            except Exception as e:
                self.message_user(request, f"Xatolik yuz berdi: {e}", level='error')