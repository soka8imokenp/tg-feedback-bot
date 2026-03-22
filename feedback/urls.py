from django.urls import path
from . import views

urlpatterns = [
    # Главная страница Mini App (Список сообщений)
    path('', views.index, name='feedback_index'),
    
    # Отправка новой формы
    path('submit/', views.submit_feedback, name='submit_feedback'),
    
    # Закрытие тикета
    path('close/<int:ticket_id>/', views.close_ticket, name='close_ticket'),

    # Ответ в существующий диалог
    path('reply/<int:ticket_id>/', views.reply_ticket, name='reply_ticket'),

    # НОВОЕ: Подгрузка дополнительных тикетов (Пагинация)
    # name='load_more_tickets' должен совпадать с тем, что мы написали в hx-get шаблона
    path('load-more/', views.load_more_tickets, name='load_more_tickets'),
]