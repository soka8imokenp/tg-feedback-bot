import os
import requests
from django.shortcuts import render
from django.http import HttpResponse
from .models import Application
from django.utils import timezone
from datetime import timedelta

# Sozlamalar
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

def index(request):
    # URL'dan user_id ni olamiz (Telegram Mini App buni yuboradi)
    user_id = request.GET.get('user_id')
    history = []
    
    if user_id:
        # Foydalanuvchining oxirgi 3 ta murojaatini olamiz
        history = Application.objects.filter(user_id=user_id).order_by('-created_at')[:3]
    
    context = {
        'history': history,
        'user_id': user_id
    }
    return render(request, 'feedback/index.html', context)

def submit_feedback(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id', 'Unknown')
        
        # --- ANTI-SPAM LOGIKA (COOLDOWN) ---
        last_app = Application.objects.filter(user_id=user_id).order_by('-created_at').first()
        
        if last_app:
            time_passed = timezone.now() - last_app.created_at
            if time_passed < timedelta(seconds=60):
                wait_time = 60 - int(time_passed.total_seconds())
                return HttpResponse(f'''
                    <div class="flex flex-col items-center justify-center h-screen space-y-6 p-8 animate-in fade-in zoom-in duration-500 bg-[#0f0f12]">
                        <div class="w-24 h-24 bg-yellow-500/10 border-2 border-yellow-500 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(234,179,8,0.2)]">
                            <svg class="w-12 h-12 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </div>
                        <div class="text-center space-y-2">
                            <h2 class="text-3xl font-bold tracking-tighter uppercase text-yellow-500">Biroz kuting</h2>
                            <p class="text-white/80 text-[10px] font-medium uppercase tracking-[2px]">
                                Iltimos, {wait_time} soniyadan so'ng qayta urining
                            </p>
                        </div>
                        <button onclick="window.location.href='/feedback/?user_id={user_id}'" 
                            class="mt-6 px-8 py-3 bg-transparent border-2 border-white/20 rounded-2xl font-bold text-[10px] text-white uppercase tracking-widest active:scale-95">
                            Orqaga
                        </button>
                    </div>
                ''')
        # --- ANTI-SPAM TUGADI ---

        username = request.POST.get('username', 'Anonymous')
        category = request.POST.get('category')
        text = request.POST.get('text')

        # 1. Ma'lumotlar bazasiga saqlash
        # Diqqat: models.py faylingda matn maydoni 'text' yoki 'message' ekanligini tekshir
        Application.objects.create(
            user_id=user_id,
            username=username,
            category=category,
            text=text 
        )

        # 2. Telegram xabari tuzilishi
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
            f"👉 <i>Javob berish uchun ushbu xabarni Reply qiling</i>\n"
            f"#id{user_id}"
        )

        # 3. Telegram API orqali yuborish
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": ADMIN_ID,
            "text": message,
            "parse_mode": "HTML"
        })

        # 4. Muvaffaqiyat ekrani
        return HttpResponse(f'''
            <div class="flex flex-col items-center justify-center h-screen space-y-6 p-8 animate-in fade-in zoom-in duration-500 bg-[#0f0f12]">
                <div class="w-24 h-24 bg-[#ad88b9]/10 border-2 border-[#ad88b9] rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(173,136,185,0.2)]">
                    <svg class="w-12 h-12 text-[#ad88b9]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
                    </svg>
                </div>
                <div class="text-center space-y-2">
                    <h2 class="text-3xl font-bold tracking-tighter uppercase">
                        <span class="text-[#ad88b9]">Qabul qilindi!</span>
                    </h2>
                    <p class="text-white/80 text-[10px] font-medium uppercase tracking-[2px]">
                        Murojaatingiz adminga yetkazildi
                    </p>
                </div>
                <button onclick="window.Telegram.WebApp.close()" 
                    class="mt-6 px-8 py-3 bg-transparent border-2 border-white/20 rounded-2xl font-bold text-[10px] text-white uppercase tracking-widest hover:border-[#ad88b9] hover:text-[#ad88b9] transition-all active:scale-95">
                    Yopish
                </button>
            </div>
        ''')

    return HttpResponse("Metod xato", status=400)