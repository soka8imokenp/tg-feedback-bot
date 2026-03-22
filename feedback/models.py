from django.db import models

class Application(models.Model):
    # Категории
    TYPES = [
        ('news', 'Yangilik yuborish'),
        ('ads', 'Reklama joylashtirish'),
        ('report', 'Shikoyat qilish'),
        ('collab', 'Hamkorlik'),
        ('other', 'Boshqa'),
    ]

    user_id = models.BigIntegerField(verbose_name="User ID")
    username = models.CharField(max_length=150, null=True, blank=True, verbose_name="Username")
    category = models.CharField(max_length=20, choices=TYPES, verbose_name="Kategoriya")
    
    # Текст пользователя
    text = models.TextField(verbose_name="Xabar matni")
    
    # Поле для ответа админа
    reply_text = models.TextField(null=True, blank=True, verbose_name="Admin javobi")
    
    # Статус: отвечено или нет
    is_answered = models.BooleanField(default=False, verbose_name="Javob berildi")

    # СТИЛЬ STEAM: Статус закрытия вопроса
    # Если True — диалог окончен, кнопка "Отправить" для этого тикета исчезнет
    is_closed = models.BooleanField(default=False, verbose_name="Yopilgan (Steam Style)")
    
    # Даты
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Oxirgi o'zgarish")

    class Meta:
        verbose_name = "Ariza"
        verbose_name_plural = "Arizalar"
        # Сортировка по обновлению: если админ ответил, тикет прыгает вверх
        ordering = ['is_closed', '-updated_at'] 

    def __str__(self):
        status = "✅" if self.is_closed else "📩"
        return f"{status} {self.category} - @{self.username}"