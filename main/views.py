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
def coming_soon(request, module_slug=None):
    """
    Hali ishlab chiqilmagan modullar uchun umumiy "tez orada" sahifasi.
    module_slug faqat URL'da qoladi (masalan statistik/tracking maqsadida),
    lekin sahifa matni umumiy va statik.
    """
    return render(request, 'coming_soon.html')