from django.db import models

class Application(models.Model):
    # Синхронизируем категории с фронтендом
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
    text = models.TextField(verbose_name="Xabar matni")
    
    # Поле для твоего ответа (чтобы история хранилась в базе)
    reply_text = models.TextField(null=True, blank=True, verbose_name="Admin javobi")
    
    # Статус: отвечено или нет
    is_answered = models.BooleanField(default=False, verbose_name="Javob berildi")
    
    # Время создания (нужно для антиспама)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan vaqt")

    class Meta:
        verbose_name = "Ariza"
        verbose_name_plural = "Arizalar"
        ordering = ['-created_at'] # Новые сообщения будут сверху

    def __str__(self):
        return f"{self.category} - @{self.username} ({self.created_at.strftime('%H:%M')})"