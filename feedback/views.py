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

def index(request):
    # Пытаемся взять user_id из GET или POST (для HTMX)
    user_id = request.GET.get('user_id') or request.POST.get('user_id')
    history = []
    
    if user_id:
        # Сначала открытые, потом закрытые. Ограничим 5 последними.
        history = Application.objects.filter(user_id=user_id).order_by('is_closed', '-updated_at')[:5]
    
    context = {
        'history': history,
        'user_id': user_id
    }
    return render(request, 'feedback/index.html', context)

def close_ticket(request, ticket_id):
    if request.method == 'POST':
        ticket = get_object_or_404(Application, id=ticket_id)
        ticket.is_closed = True
        ticket.save()
        
        # После закрытия возвращаем обновленную страницу
        return index(request)
    return HttpResponse("Metod xato", status=400)

def reply_ticket(request, ticket_id):
    """Добавление сообщения клиента в существующий диалог"""
    if request.method == 'POST':
        ticket = get_object_or_404(Application, id=ticket_id)
        new_reply = request.POST.get('new_reply')
        
        if new_reply and not ticket.is_closed:
            # Склеиваем старый текст с новым
            ticket.text += f"\n\n[Mijoz]: {new_reply}"
            ticket.updated_at = timezone.now() # Обновляем дату, чтобы тикет поднялся выше
            ticket.save()
            
            # Уведомляем админа о новом сообщении в старом тикете
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            tg_message = (
                f"💬 <b>#id{ticket.user_id} dan yangi xabar!</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"<b>Mavzu:</b> {ticket.category}\n"
                f"<b>Xabar:</b> {new_reply}\n\n"
                f"👉 <i>Javob berish uchun #id{ticket.user_id} ga Reply qiling</i>"
            )
            try:
                requests.post(url, data={"chat_id": ADMIN_ID, "text": tg_message, "parse_mode": "HTML"}, timeout=5)
            except:
                pass
                
        return index(request)
    return HttpResponse("Metod xato", status=400)

def submit_feedback(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id', 'Unknown')
        
        # --- ANTI-SPAM LOGIKA ---
        last_app = Application.objects.filter(user_id=user_id).order_by('-created_at').first()
        
        if last_app:
            time_passed = timezone.now() - last_app.created_at
            if time_passed < timedelta(seconds=60):
                wait_time = 60 - int(time_passed.total_seconds())
                return HttpResponse(f'''
                    <div class="flex flex-col items-center justify-center h-screen space-y-6 p-8 bg-[#0f0f12]">
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
        text = request.POST.get('text')

        # 1. Сохраняем в базу
        Application.objects.create(
            user_id=user_id,
            username=username,
            category=category,
            text=text 
        )

        # 2. Telegram xabari
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
            f"<b>Kimdan:</b> @{username}\n"
            f"<b>ID:</b> <code>{user_id}</code>\n"
            f"<b>Matn:</b> {text}\n\n"
            f"👉 <i>Javob uchun Reply qiling</i>\n"
            f"#id{user_id}"
        )

        # 3. Отправка админу
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": ADMIN_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
        except Exception as e:
            print(f"Telegram error: {e}")

        # 4. Success Screen
        return HttpResponse(f'''
            <div class="flex flex-col items-center justify-center h-screen space-y-6 p-8 bg-[#0c0a14]">
                <script>window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');</script>
                <div class="w-24 h-24 bg-[#ad88b9]/20 border-2 border-[#ad88b9] rounded-full flex items-center justify-center animate-bounce">
                    <svg class="w-12 h-12 text-[#ad88b9]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
                    </svg>
                </div>
                <h2 class="text-2xl font-bold text-white uppercase tracking-tighter">Yuborildi!</h2>
                <button onclick="window.location.reload()" class="px-10 py-4 bg-[#ad88b9] border-2 border-black shadow-[4px_4px_0px_#000] rounded-2xl text-white font-bold uppercase text-[10px]">Orqaga</button>
            </div>
        ''')

    return HttpResponse("Metod xato", status=400)