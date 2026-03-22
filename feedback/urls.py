from django.urls import path
from . import views

urlpatterns = [
    # Главная страница Mini App (Список сообщений)
    path('', views.index, name='feedback_index'),
    
    # Отправка новой формы
    path('submit/', views.submit_feedback, name='submit_feedback'),
    
    # СТИЛЬ STEAM: Закрытие тикета (обработка нажатия кнопки "Masalani yopish")
    path('close/<int:ticket_id>/', views.close_ticket, name='close_ticket'),

    # НОВОЕ: Ответ в существующий диалог (чат внутри карточки)
    path('reply/<int:ticket_id>/', views.reply_ticket, name='reply_ticket'),
]