from django.contrib import admin
from django.urls import path, include  # Импортируй include!

urlpatterns = [
    path('admin/', admin.site.urls),
    # Эта строка говорит Django: "Если адрес начинается с /feedback/, 
    # ищи дальнейшие инструкции в файле feedback.urls"
    path('feedback/', include('feedback.urls')), 
]