import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') # Проверь имя папки с настройками
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'tokimachinedesu@gmail.com', 'devve08082002')
    print("Admin created!")
else:
    print("Admin already exists.")