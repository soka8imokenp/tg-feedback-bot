import os
import requests
from django.contrib import admin
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    # Поля, которые видны в списке заявок
    # Добавил 'reply_text', чтобы ты видел ответ прямо в таблице
    list_display = ('username', 'category', 'created_at', 'is_answered')
    list_filter = ('category', 'created_at')
    
    # Метод для отображения иконки (галочки) в списке
    def is_answered(self, obj):
        # Проверяем именно поле reply_text
        return bool(obj.reply_text)
    
    is_answered.boolean = True
    is_answered.short_description = "Javob berildi"

    def save_model(self, request, obj, form, change):
        # 1. Сначала сохраняем данные в базу (Django запишет reply_text)
        super().save_model(request, obj, form, change)

        # 2. Если поле ответа (reply_text) заполнено, отправляем уведомление в Telegram
        if obj.reply_text:
            bot_token = os.getenv("BOT_TOKEN")
            user_id = obj.user_id # Убедись, что это поле есть в модели
            
            text = (
                f"<b>📩 Sizning murojaatingizga javob keldi!</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"<b>Sizning xabaringiz:</b>\n<i>{obj.text}</i>\n\n"
                f"<b>Admin javobi:</b>\n✅ {obj.reply_text}\n"
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
                    self.message_user(request, f"Javob @{obj.username} ga Telegram orqali yuborildi.")
                else:
                    # Если ошибка от Telegram (например, юзер заблокировал бота)
                    self.message_user(request, f"Telegramga yuborishda xatolik (Status: {response.status_code}).", level='error')
            except Exception as e:
                self.message_user(request, f"Xatolik yuz berdi: {e}", level='error')