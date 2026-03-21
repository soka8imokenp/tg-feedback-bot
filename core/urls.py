from django.contrib.auth.models import User
import os

# Скрипт для автоматического создания админа в новой базе
try:
    # Проверяем, существует ли уже такой юзер, чтобы не было ошибки
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin', 
            email='admin@example.com', 
            password='devve08082002'  # <--- ПИШИ ПАРОЛЬ ТУТ
        )
        print("--- СУПЕРЮЗЕР СОЗДАН УСПЕШНО ---")
except Exception as e:
    # Если база еще не готова или таблиц нет, просто пропустим
    print(f"--- Ошибка авто-админа: {e} ---")