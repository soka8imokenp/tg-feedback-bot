from django.contrib import admin
from django import forms
from django.utils import timezone
from .models import Application

class ApplicationAdmin(admin.ModelAdmin):
    # Что отображать в списке всех заявок
    list_display = ('subject', 'username', 'category', 'is_answered', 'is_closed', 'created_at')
    list_filter = ('is_closed', 'category', 'is_answered')
    
    # Поля, которые нельзя редактировать вручную (чтобы не сломать JSON)
    readonly_fields = ('chat_history', 'created_at', 'updated_at')
    
    # Добавляем свое поле для ответа прямо в форму редактирования
    fieldsets = (
        ('Ma\'lumotlar', {
            'fields': ('user_id', 'username', 'category', 'subject', 'is_closed', 'is_answered')
        }),
        ('Chat tarixi', {
            'fields': ('chat_history',),
        }),
        ('Javob berish', {
            'fields': ('admin_reply_field',),
            'description': 'Bu yerga yozilgan xabar mijozga chatga boradi.',
        }),
    )

    # Создаем виртуальное поле для ввода текста
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['admin_reply_field'] = forms.CharField(
            widget=forms.Textarea(attrs={'rows': 4, 'style': 'width: 100%;'}),
            required=False,
            label="Admin javobi"
        )
        return form

    # Логика сохранения ответа
    def save_model(self, request, obj, form, change):
        reply_text = form.cleaned_data.get('admin_reply_field')
        
        if reply_text:
            # Формируем объект сообщения
            new_message = {
                'role': 'admin',
                'text': reply_text,
                'time': timezone.now().strftime("%H:%M")
            }
            
            # Добавляем в JSON историю
            history = list(obj.chat_history)
            history.append(new_message)
            obj.chat_history = history
            
            # Ставим отметку, что ответ дан
            obj.is_answered = True
            
            # ТУТ МОЖНО ДОБАВИТЬ ОТПРАВКУ В ТЕЛЕГРАМ ПОЛЬЗОВАТЕЛЮ, ЕСЛИ НУЖНО
            # (вызов функции отправки сообщения ботом)

        super().save_model(request, obj, form, change)

admin.site.register(Application, ApplicationAdmin)