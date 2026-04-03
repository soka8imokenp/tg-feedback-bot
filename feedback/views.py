import os
import requests
from datetime import timedelta
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.utils import timezone


from .models import Application, Message, Profile

# Sozlamalar
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")

def get_history_context(user_id, limit=5, offset=0):
    """
    Вспомогательная функция для получения истории и флагов пагинации.
    """
    total_count = Application.objects.filter(user_id=user_id).count()
    history = Application.objects.filter(user_id=user_id).order_by('is_closed', '-updated_at')[offset:offset + limit]
    
    new_offset = offset + limit
    has_more = total_count > new_offset
    
    return {
        'history': history,
        'user_id': user_id,
        'next_offset': new_offset,
        'has_more_tickets': has_more
    }


def get_staff_user_by_telegram_id(user_id):
    """Возвращает staff-пользователя, если найден по telegram_id."""
    if not user_id:
        return None

    try:
        telegram_id = int(user_id)
    except (TypeError, ValueError):
        return None

    profile = (
        Profile.objects
        .select_related('user')
        .filter(telegram_id=telegram_id, user__is_staff=True)
        .first()
    )
    return profile.user if profile else None


def _staff_from_request(request):
    user_id = request.GET.get('user_id') or request.POST.get('user_id')
    return user_id, get_staff_user_by_telegram_id(user_id)


def _build_ticket_messages(ticket):
    """Нормализованный список сообщений для шаблона админ-чата."""
    db_messages = list(ticket.messages.all().order_by('created_at'))
    if db_messages:
        return [
            {
                'text': item.text,
                'is_from_admin': item.is_from_admin,
                'time': timezone.localtime(item.created_at).strftime('%H:%M'),
            }
            for item in db_messages
        ]

    # Fallback на legacy JSON-историю
    normalized = []
    for msg in ticket.chat_history or []:
        normalized.append(
            {
                'text': msg.get('text', ''),
                'is_from_admin': msg.get('role') == 'admin',
                'time': msg.get('time', ''),
            }
        )
    return normalized


def _send_admin_notification(ticket, message_text):
    """Уведомление админу без кнопок."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_ID,
        "text": message_text,
        "parse_mode": "HTML",
    }

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass


def index(request):
    user_id = request.GET.get('user_id') or request.POST.get('user_id')

    # Step 2: универсальный logic gate для admin/user интерфейса
    staff_user = get_staff_user_by_telegram_id(user_id)
    if staff_user:
        tickets = Application.objects.order_by('is_closed', 'is_answered', '-updated_at')
        selected_ticket = tickets.first()
        return render(request, 'feedback/admin_dashboard.html', {
            'user_id': user_id,
            'staff_user': staff_user,
            'tickets': tickets,
            'selected_ticket': selected_ticket,
            'messages': _build_ticket_messages(selected_ticket) if selected_ticket else [],
        })

    context = {'user_id': user_id}
    
    if user_id:
        limit = int(request.GET.get('limit', 5))
        history_data = get_history_context(user_id, limit=limit)
        context.update(history_data)
    
    return render(request, 'feedback/index.html', context)


def admin_ticket_chat(request, ticket_id):
    user_id, staff_user = _staff_from_request(request)
    if not staff_user:
        return HttpResponseForbidden("Staff only")

    ticket = get_object_or_404(Application, id=ticket_id)
    messages = _build_ticket_messages(ticket)

    return render(request, 'feedback/partials/admin_ticket_chat.html', {
        'user_id': user_id,
        'staff_user': staff_user,
        'selected_ticket': ticket,
        'messages': messages,
    })


def admin_reply_ticket(request, ticket_id):
    user_id, staff_user = _staff_from_request(request)
    if not staff_user:
        return HttpResponseForbidden("Staff only")

    if request.method != 'POST':
        return HttpResponse("Metod xato", status=400)

    ticket = get_object_or_404(Application, id=ticket_id)
    reply_text = (request.POST.get('reply_text') or '').strip()

    if reply_text and not ticket.is_closed:
        Message.objects.create(application=ticket, text=reply_text, is_from_admin=True)

        # Backward compatibility: duplicate in legacy JSON.
        chat_history = list(ticket.chat_history or [])
        chat_history.append({
            'role': 'admin',
            'text': reply_text,
            'time': timezone.now().strftime("%H:%M"),
        })
        ticket.chat_history = chat_history

        ticket.is_answered = True
        ticket.updated_at = timezone.now()
        ticket.save()

    return admin_ticket_chat(request, ticket_id)


def admin_close_ticket(request, ticket_id):
    if request.method != 'POST':
        return HttpResponse("Metod xato", status=400)

    ticket = get_object_or_404(Application, id=ticket_id)
    ticket.is_closed = True
    ticket.updated_at = timezone.now()
    ticket.save()

    return admin_ticket_chat(request, ticket_id)

           

def load_more_tickets(request):
    user_id = request.GET.get('user_id')
    offset = int(request.GET.get('offset', 0))
    limit = 5
    if not user_id:
        return HttpResponse("")

    context = get_history_context(user_id, limit=limit, offset=offset)
    return render(request, 'feedback/partials/ticket_list.html', context)


def close_ticket(request, ticket_id):
    if request.method == 'POST':
        ticket = get_object_or_404(Application, id=ticket_id)
        ticket.is_closed = True
        ticket.save()
        
        user_id = request.POST.get('user_id') or ticket.user_id
        # Получаем данные истории
        context = get_history_context(user_id)
        # Обязательно добавляем user_id в контекст явно, если шаблон его ждет
        context['user_id'] = user_id 
        
        return render(request, 'feedback/index.html', context)
    return HttpResponse("Metod xato", status=400)


def reply_ticket(request, ticket_id):
    """
    Когда клиент дописывает сообщение в Web App.
    """
    if request.method == 'POST':
        ticket = get_object_or_404(Application, id=ticket_id)
        new_reply = request.POST.get('new_reply')
        
        if new_reply and not ticket.is_closed:
            # Новый формат
            Message.objects.create(application=ticket, text=new_reply, is_from_admin=False)

            # Legacy fallback
            message_obj = {
                'role': 'user',
                'text': new_reply,
                'time': timezone.now().strftime("%H:%M")
            }
            
            chat_history = list(ticket.chat_history)
            chat_history.append(message_obj)
            ticket.chat_history = chat_history
            
            ticket.updated_at = timezone.now()
            ticket.is_answered = False 
            ticket.save()
            
            
            tg_message = (
                f"💬 <b>#id{ticket.user_id} dan yangi xabar!</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"<b>Mavzu:</b> {ticket.subject}\n"
                f"<b>Xabar:</b> {new_reply}\n\n"
                f"👉 <i>Javob uchun #id{ticket.user_id} ga Reply qiling</i>"
            )
            _send_admin_notification(ticket, tg_message)
                
        user_id = request.POST.get('user_id') or ticket.user_id
        context = get_history_context(user_id)
        return render(request, 'feedback/index.html', context)
    return HttpResponse("Metod xato", status=400)

def submit_feedback(request):
    """
    Создание нового тикета. Исправлен ответ для HTMX.
    """
    if request.method == 'POST':
        user_id = request.POST.get('user_id', 'Unknown')
        
        # Анти-спам
        last_app = Application.objects.filter(user_id=user_id).order_by('-created_at').first()
        if last_app:
            time_passed = timezone.now() - last_app.created_at
            if time_passed < timedelta(seconds=60):
                wait_time = 60 - int(time_passed.total_seconds())
                return HttpResponse(f'''
                    <div id="form-container" class="flex flex-col items-center justify-center h-screen space-y-6 p-8 bg-[#0c0a14]">
                        <script>window.Telegram.WebApp.HapticFeedback.notificationOccurred('warning');</script>
                        <div class="w-24 h-24 bg-yellow-500/10 border-2 border-yellow-500 rounded-full flex items-center justify-center">
                            <svg class="w-12 h-12 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </div>
                        <h2 class="text-2xl font-bold text-yellow-500 uppercase">Kutib turing</h2>
                        <p class="text-white/60 text-center uppercase text-[10px] tracking-widest">Iltimos, {wait_time} soniyadan so'ng urinib ko'ring</p>
                        <button onclick="window.location.reload()" class="px-8 py-3 border-2 border-white/20 rounded-2xl text-white text-[10px] font-bold uppercase">Yangilash</button>
                    </div>
                ''')

        username = request.POST.get('username', 'Anonymous')
        category = request.POST.get('category', 'other')
        subject = request.POST.get('subject', "Mavzu ko'rsatilmadi")
        text = request.POST.get('text')

        application = Application.objects.create(
            user_id=user_id, username=username,
            category=category, subject=subject,
            chat_history=[{'role': 'user', 'text': text, 'time': timezone.now().strftime("%H:%M")}]
        )
        Message.objects.create(application=application, text=text, is_from_admin=False)

        category_config = {
            'news': ('📢', 'YANGILIK'),
            'ads': ('💰', 'REKLAMA'),
            'report': ('⚠️', 'SHIKOYAT'),
            'collab': ('🤝', 'HAMKORLIK'),
            'other': ('💬', 'BOSHQA')
        }
        icon, title = category_config.get(category, ('📩', 'YANGI XABAR'))

        message = (
            f"<b>{icon} {title}</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"<b>Mavzu:</b> {subject}\n"
            f"<b>Kimdan:</b> @{username}\n"
            f"<b>ID:</b> <code>{user_id}</code>\n"
            f"<b>Matn:</b> {text}\n\n"
            f"👉 <i>Javob uchun Reply qiling</i>\n"
            f"#id{user_id}"
        )

        _send_admin_notification(application, message)

        # Исправленный блок успеха (добавлен текст и кнопка Orqaga)
        return HttpResponse(f'''
            <div id="form-container" class="flex flex-col items-center justify-center h-screen space-y-6 p-8 bg-[#0c0a14]">
                <script>window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');</script>
                <div class="w-24 h-24 bg-[#ad88b9]/20 border-2 border-[#ad88b9] rounded-full flex items-center justify-center animate-bounce">
                    <svg class="w-12 h-12 text-[#ad88b9]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
                    </svg>
                </div>
                <div class="text-center space-y-2">
                    <h2 class="text-2xl font-bold text-white uppercase tracking-tighter">Yuborildi!</h2>
                    <p class="text-[10px] text-white/50 font-bold uppercase tracking-widest">Tez orada javob beramiz</p>
                </div>
                <button onclick="window.Telegram.WebApp.HapticFeedback.impactOccurred('medium'); window.location.reload();" 
                        class="px-10 py-4 bg-[#ad88b9] border-2 border-black shadow-[4px_4px_0px_#000] rounded-2xl text-white font-bold uppercase text-[10px] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all">
                    Orqaga
                </button>
            </div>
        ''')

    return HttpResponse("Metod xato", status=400)