import os
import requests
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Application
from django.utils import timezone
from datetime import timedelta

# Sozlamalar
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

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

def index(request):
    user_id = request.GET.get('user_id') or request.POST.get('user_id')
    context = {'user_id': user_id}
    
    if user_id:
        limit = int(request.GET.get('limit', 5))
        history_data = get_history_context(user_id, limit=limit)
        context.update(history_data)
    
    return render(request, 'feedback/index.html', context)

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
        context = get_history_context(user_id)
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
            
            # Уведомление админу
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            tg_message = (
                f"💬 <b>#id{ticket.user_id} dan yangi xabar!</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"<b>Mavzu:</b> {ticket.subject}\n"
                f"<b>Xabar:</b> {new_reply}\n\n"
                f"👉 <i>Javob uchun #id{ticket.user_id} ga Reply qiling</i>"
            )
            try:
                requests.post(url, data={"chat_id": ADMIN_ID, "text": tg_message, "parse_mode": "HTML"}, timeout=5)
            except:
                pass
                
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

        Application.objects.create(
            user_id=user_id, username=username,
            category=category, subject=subject,
            chat_history=[{'role': 'user', 'text': text, 'time': timezone.now().strftime("%H:%M")}]
        )

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

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": ADMIN_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
        except:
            pass

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