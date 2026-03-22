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
    
    # Тема обращения
    subject = models.CharField(max_length=50, verbose_name="Mavzu", default="Mavzu ko'rsatilmadi")
    
    # --- НОВОЕ: ИСТОРИЯ ЧАТА В ФОРМАТЕ JSON ---
    # Храним список вида: [{"role": "user", "text": "...", "date": "..."}, ...]
    chat_history = models.JSONField(default=list, verbose_name="Chat tarixi", blank=True)
    
    # Статус: отвечено или нет
    is_answered = models.BooleanField(default=False, verbose_name="Javob berildi")

    # Статус закрытия вопроса
    is_closed = models.BooleanField(default=False, verbose_name="Yopilgan")
    
    # Даты
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Oxirgi o'zgarish")

    class Meta:
        verbose_name = "Ariza"
        verbose_name_plural = "Arizalar"
        ordering = ['is_closed', '-updated_at'] 

    def __str__(self):
        status = "✅" if self.is_closed else "📩"
        return f"{status} [{self.category}] {self.subject} - @{self.username}"