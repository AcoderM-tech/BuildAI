from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decouple import config
import json
import urllib.error
import urllib.request
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .forms import RegisterForm
from .models import Calculation, Project


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

COPILOT_WORKER_URL = config(
    "COPILOT_WORKER_URL",
    default="https://little-cloud-199e.avazbekmexriddinov63.workers.dev",
)


def _call_copilot_worker(prompt):
    """Send a prompt to the already-deployed Cloudflare Worker."""
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    request = urllib.request.Request(
        COPILOT_WORKER_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("AI Worker bilan bog‘lanib bo‘lmadi.") from exc

    if not isinstance(data, dict) or data.get("status") != "success":
        raise RuntimeError(data.get("error", "AI Worker javob bermadi."))

    answer = data.get("response")
    if not answer:
        raise RuntimeError("AI Worker bo‘sh javob qaytardi.")

    return str(answer)


def _user_copilot_context(user):
    """Build a private, user-scoped snapshot. Never queries another user's projects."""
    projects = Project.objects.filter(user=user).prefetch_related("drawings")
    context = {
        "user": {
            "first_name": user.first_name or "",
            "username": user.username or "",
        },
        "projects": [],
    }

    for project in projects:
        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "drawings": [],
        }

        for drawing in project.drawings.all():
            drawing_data = {
                "id": drawing.id,
                "original_name": drawing.original_name or drawing.file.name,
                "file_type": drawing.file_type,
                "status": drawing.status,
                "created_at": drawing.created_at.isoformat(),
                "processed_at": drawing.processed_at.isoformat() if drawing.processed_at else None,
                "calculations": [],
            }

            calculations = Calculation.objects.filter(drawing=drawing).prefetch_related("items__material")
            for calculation in calculations:
                calculation_data = {
                    "id": calculation.id,
                    "status": calculation.status,
                    "total_area": str(calculation.total_area) if calculation.total_area is not None else None,
                    "total_wall_length": str(calculation.total_wall_length) if calculation.total_wall_length is not None else None,
                    "total_material_cost": str(calculation.total_material_cost),
                    "currency": calculation.currency,
                    "error_message": calculation.error_message,
                    "created_at": calculation.created_at.isoformat(),
                    "updated_at": calculation.updated_at.isoformat(),
                    "items": [],
                }

                for item in calculation.items.all():
                    calculation_data["items"].append({
                        "material": item.material.name,
                        "quantity": str(item.quantity),
                        "unit": item.unit,
                        "unit_price": str(item.unit_price),
                        "total_price": str(item.total_price),
                    })

                drawing_data["calculations"].append(calculation_data)

            project_data["drawings"].append(drawing_data)

        context["projects"].append(project_data)

    return context


@login_required(login_url="login")
def copilot_page(request):
    """Private AI Copilot workspace."""
    projects = Project.objects.filter(user=request.user)
    return render(
        request,
        "copilot.html",
        {
            "projects": projects,
            "projects_count": projects.count(),
        },
    )


@require_POST
def copilot_public_chat_api(request):
    """Public landing-page chat: general BuildAI/construction answers only."""
    try:
        body = json.loads(request.body or "{}")
        message = str(body.get("message", "")).strip()
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Noto‘g‘ri so‘rov."}, status=400)

    if not message:
        return JsonResponse({"error": "Savol kiriting."}, status=400)
    if len(message) > 4000:
        return JsonResponse({"error": "Savol juda uzun."}, status=400)

    try:
        answer = _call_copilot_worker(message)
    except RuntimeError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    return JsonResponse({"response": answer})


@login_required(login_url="login")
@require_POST
def copilot_chat_api(request):
    """Private Copilot API. The Worker receives only this user's project data."""
    try:
        body = json.loads(request.body or "{}")
        message = str(body.get("message", "")).strip()
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Noto‘g‘ri so‘rov."}, status=400)

    if not message:
        return JsonResponse({"error": "Savol kiriting."}, status=400)
    if len(message) > 4000:
        return JsonResponse({"error": "Savol juda uzun."}, status=400)

    private_context = _user_copilot_context(request.user)
    prompt = (
        "Foydalanuvchi savoliga javob ber. Quyidagi PRIVATE_BUILDai_USER_CONTEXT faqat "
        "shu autentifikatsiyadan o'tgan foydalanuvchiga tegishli. Undagi ma'lumotlarni boshqa "
        "foydalanuvchi ma'lumotlari bilan aralashtirma va mavjud bo'lmagan ma'lumotni o'ylab topma. "
        "Agar savol loyiha ma'lumotiga taalluqli bo'lmasa, oddiy umumiy javob ber.\n\n"
        "PRIVATE_BUILDAI_USER_CONTEXT:\n"
        f"{json.dumps(private_context, ensure_ascii=False, default=str)}\n\n"
        "USER_QUESTION:\n"
        f"{message}"
    )

    try:
        answer = _call_copilot_worker(prompt)
    except RuntimeError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    return JsonResponse({"response": answer})
