from django.contrib import admin
from django import forms
from django.utils import timezone
from .models import Application

# 1. Создаем правильную форму для админки с нашим кастомным полем
class ApplicationAdminForm(forms.ModelForm):
    admin_reply_field = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4, 
            'style': 'width: 100%; border: 2px solid #444; border-radius: 8px; padding: 10px;',
            'placeholder': 'Mijozga xabar yozing...'
        }),
        required=False, # Поле не обязательно для заполнения
        label="Admin javobi"
    )

    class Meta:
        model = Application
        fields = '__all__'


# 2. Подключаем форму в админку
class ApplicationAdmin(admin.ModelAdmin):
    # Указываем Django использовать нашу форму!
    form = ApplicationAdminForm

    # Настройки списка
    list_display = ('subject', 'username', 'category', 'is_answered', 'is_closed', 'created_at')
    list_filter = ('is_closed', 'category', 'is_answered')
    
    # Поля только для чтения
    readonly_fields = ('chat_history', 'created_at', 'updated_at')
    
    # Группировка полей
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('user_id', 'username', 'category', 'subject', 'is_closed', 'is_answered')
        }),
        ('Chat', {
            'fields': ('chat_history',),
        }),
        ('Javob berish', {
            'fields': ('admin_reply_field',),
            'description': 'Bu yerga yozilgan xabar Web App ichidagi chatda paydo bo\'ladi.',
        }),
    )

    # Логика сохранения
    def save_model(self, request, obj, form, change):
        # Достаем текст из нашей кастомной формы
        reply_text = form.cleaned_data.get('admin_reply_field')
        
        if reply_text:
            new_message = {
                'role': 'admin',
                'text': reply_text,
                'time': timezone.now().strftime("%H:%M")
            }
            
            # Обновляем JSON
            history = list(obj.chat_history) if obj.chat_history else []
            history.append(new_message)
            obj.chat_history = history
            
            obj.is_answered = True

        super().save_model(request, obj, form, change)

admin.site.register(Application, ApplicationAdmin)