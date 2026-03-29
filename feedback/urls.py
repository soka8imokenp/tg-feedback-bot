from django.urls import path
from . import views

# Рекомендуется добавить app_name, если проект будет расти
app_name = 'feedback' 

urlpatterns = [
    # Главная страница (Список тикетов)
    path('', views.index, name='feedback_index'),

    # Admin WebApp panel
    path('admin/ticket/<int:ticket_id>/chat/', views.admin_ticket_chat, name='admin_ticket_chat'),
    path('admin/ticket/<int:ticket_id>/reply/', views.admin_reply_ticket, name='admin_reply_ticket'),

    # User WebApp flow
    path('submit/', views.submit_feedback, name='submit_feedback'),
    
    # Закрытие тикета (убедитесь, что в views.py функция принимает ticket_id)
    path('close/<int:ticket_id>/', views.close_ticket, name='close_ticket'),

    # Ответ в существующий диалог
    path('reply/<int:ticket_id>/', views.reply_ticket, name='reply_ticket'),

    # Подгрузка дополнительных тикетов (AJAX/HTMX)
    path('load-more/', views.load_more_tickets, name='load_more_tickets'),
]