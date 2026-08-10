from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .forms import RegisterForm
from .models import Project


def landing_page(request):
    """
    BuildAI Landing Page and MVP Engine view.
    Renders templates/landing.html
    """
    return render(request, 'landing.html')


def about_page(request):
    """
    Haqimizda (About Us) sahifasini ko'rsatish uchun view.
    """
    return render(request, 'about.html')


def login_page(request):
    """
    Kirish (Login) sahifasi — GET'da forma, POST'da autentifikatsiya.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        next_url = request.POST.get('next') or request.GET.get('next')
        return redirect(next_url or 'dashboard')

    return render(request, 'login.html', {'form': form})


def register_page(request):
    """
    Ro'yxatdan o'tish sahifasi — GET'da forma, POST'da yangi foydalanuvchi yaratish.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Xush kelibsiz! Ro'yxatdan muvaffaqiyatli o'tdingiz.")
        return redirect('dashboard')

    return render(request, 'registr.html', {'form': form})


def logout_view(request):
    """
    Tizimdan chiqish — faqat POST orqali chaqirilishi tavsiya etiladi.
    """
    logout(request)
    return redirect('landing_page')


@login_required(login_url='login')
def dashboard_view(request):
    """
    Foydalanuvchining shaxsiy boshqaruv paneli — o'z loyihalari va statistikasi.
    """
    projects = Project.objects.filter(user=request.user)

    context = {
        'projects': projects,
        'projects_count': projects.count(),
        'active_count': projects.filter(status='active').count(),
        'completed_count': projects.filter(status='completed').count(),
        'draft_count': projects.filter(status='draft').count(),
    }
    return render(request, 'dashboard.html', context)
@login_required
def coming_soon(request, module_slug):
    modules = {
        "buyurtmalar": {
            "name": "Buyurtmalar",
            "icon": "fa-solid fa-clipboard-list",
            "description": (
                "Qurilish buyurtmalarini yaratish, boshqarish va "
                "loyiha jarayonlarini bir joydan nazorat qilish imkoniyati."
            ),
        },

        "smeta-hisobotlari": {
            "name": "Smeta Hisobotlari",
            "icon": "fa-solid fa-file-invoice-dollar",
            "description": (
                "Loyihalar bo‘yicha smeta hisobotlarini yaratish, "
                "ko‘rish va yuklab olish imkoniyati."
            ),
        },

        "chizmalar-cad": {
            "name": "Chizmalar va CAD",
            "icon": "fa-solid fa-drafting-compass",
            "description": (
                "Qurilish chizmalarini ko‘rish, tahrirlash va "
                "kelajakda BuildAI ichida CAD vositalari bilan ishlash."
            ),
        },

        "materiallar": {
            "name": "Materiallar Katalogi",
            "icon": "fa-solid fa-boxes-stacked",
            "description": (
                "Mahalliy do‘konlar va yetkazib beruvchilarning "
                "qurilish materiallari, narxlari va mavjudligini bir joyda ko‘rish."
            ),
        },

        "pudratchilar": {
            "name": "Pudratchilar Bazasi",
            "icon": "fa-solid fa-users-gear",
            "description": (
                "Ishonchli pudratchilarni topish, xizmatlarini ko‘rish "
                "va kelajakda reyting hamda ishonchlilik ko‘rsatkichlarini baholash."
            ),
        },

        "shnq": {
            "name": "ShNQ Normativlari",
            "icon": "fa-solid fa-book-open",
            "description": (
                "Qurilish standartlari, me’yorlari va normativ hujjatlarini "
                "loyiha jarayonida tezkor izlash va qo‘llash."
            ),
        },

        "tariflar": {
            "name": "Tariflar va Rejalar",
            "icon": "fa-solid fa-credit-card",
            "description": (
                "BuildAI xizmatlari uchun tariflar, obuna rejalarini "
                "tanlash va foydalanish imkoniyatlarini boshqarish."
            ),
        },

        "sozlamalar": {
            "name": "Sozlamalar",
            "icon": "fa-solid fa-sliders",
            "description": (
                "Profil, platforma va foydalanuvchi sozlamalarini "
                "boshqarish imkoniyati."
            ),
        },
    }

    module = modules.get(module_slug)

    if not module:
        module = {
            "name": "Ushbu modul",
            "icon": "fa-solid fa-screwdriver-wrench",
            "description": (
                "Ushbu modul BuildAI platformasining keyingi "
                "rivojlanish bosqichida ishga tushiriladi."
            ),
        }

    context = {
        "module_name": module["name"],
        "module_icon": module["icon"],
        "module_description": module["description"],
    }

    return render(
        request,
        "coming_soon.html",
        context
    )