from django.contrib import admin
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    # Список полей, которые будут видны в таблице
    list_display = ('username', 'category', 'created_at', 'is_answered')
    
    # Фильтры справа
    list_filter = ('category', 'is_answered', 'created_at')
    
    # Поиск по тексту и юзернейму
    search_fields = ('username', 'text', 'user_id')
    
    # Чтобы нельзя было случайно изменить ID пользователя в админке
    readonly_fields = ('created_at',)