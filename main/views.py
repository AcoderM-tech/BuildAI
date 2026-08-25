import json
import urllib.error
import urllib.request

from decouple import config
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import RegisterForm
from .models import Calculation, Project


# ============================================================
# LANDING
# ============================================================

def landing_page(request):
    return render(request, "landing.html")


# ============================================================
# ABOUT
# ============================================================

def about_page(request):
    return render(request, "about.html")


# ============================================================
# AUTH
# ============================================================

def login_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        next_url = request.POST.get("next") or request.GET.get("next")
        return redirect(next_url or "dashboard")

    return render(request, "login.html", {"form": form})


def register_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Xush kelibsiz! Ro'yxatdan muvaffaqiyatli o'tdingiz.")
        return redirect("dashboard")

    return render(request, "registr.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("landing_page")


# ============================================================
# DASHBOARD
# ============================================================

@login_required(login_url="login")
def dashboard_view(request):
    projects = Project.objects.filter(user=request.user)

    context = {
        "projects": projects,
        "projects_count": projects.count(),
        "active_count": projects.filter(status="active").count(),
        "completed_count": projects.filter(status="completed").count(),
        "draft_count": projects.filter(status="draft").count(),
    }

    return render(request, "dashboard.html", context)


# ============================================================
# COMING SOON
# ============================================================

@login_required
def coming_soon(request, module_slug=None):
    return render(request, "coming_soon.html")


# ============================================================
# OPENROUTER AI — config
# ============================================================

OPENROUTER_API_KEY = config("OPENROUTER_API_KEY", default="")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = config("OPENROUTER_MODEL", default="stealth/ox-alpha")


# ============================================================
# OPENROUTER — asosiy chaqiruv funksiyasi
# ============================================================

def _call_openrouter(prompt: str) -> str:
    """
    OpenRouter API ga POST so'rov yuboradi va AI javobini qaytaradi.

    Prompt oddiy matn sifatida user xabari sifatida yuboriladi.
    Reasoning yoqilgan holda so'rov yuboriladi.
    """

    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY sozlanmagan.")

    payload = json.dumps(
        {
            "model": OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "reasoning": {"enabled": True},
        },
        ensure_ascii=False,
    ).encode("utf-8")

    api_request = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    # --------------------------------------------------------
    # HTTP REQUEST
    # --------------------------------------------------------

    try:
        with urllib.request.urlopen(api_request, timeout=60) as response:
            raw_response = response.read().decode("utf-8")

    except urllib.error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            error_body = ""
        raise RuntimeError(
            f"OpenRouter HTTP {exc.code}: {error_body[:1000]}"
        ) from exc

    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", "Noma'lum ulanish xatosi")
        raise RuntimeError(
            f"OpenRouter bilan ulanib bo'lmadi: {reason}"
        ) from exc

    except TimeoutError as exc:
        raise RuntimeError(
            "OpenRouter ajratilgan vaqt ichida javob bermadi."
        ) from exc

    except Exception as exc:
        raise RuntimeError(f"OpenRouter xatosi: {str(exc)}") from exc

    # --------------------------------------------------------
    # JSON PARSE
    # --------------------------------------------------------

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"OpenRouter JSON formatida javob qaytarmadi.\n{raw_response[:1000]}"
        ) from exc

    # --------------------------------------------------------
    # JAVOBNI OLISH
    # --------------------------------------------------------

    try:
        answer = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        error = data.get("error", {})
        if isinstance(error, dict):
            error = error.get("message", "")
        raise RuntimeError(
            f"OpenRouter javobida matn topilmadi. "
            f"Xato: {error or raw_response[:500]}"
        )

    if not answer:
        raise RuntimeError("OpenRouter bo'sh javob qaytardi.")

    return str(answer)


# ============================================================
# PRIVATE USER CONTEXT
# ============================================================

def _user_copilot_context(user):
    """
    Faqat autentifikatsiyadan o'tgan foydalanuvchining
    ma'lumotlarini Copilot uchun tayyorlaydi.
    """

    projects = (
        Project.objects
        .filter(user=user)
        .prefetch_related("drawings")
    )

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
            "created_at": (
                project.created_at.isoformat() if project.created_at else None
            ),
            "updated_at": (
                project.updated_at.isoformat() if project.updated_at else None
            ),
            "drawings": [],
        }

        for drawing in project.drawings.all():

            drawing_data = {
                "id": drawing.id,
                "original_name": drawing.original_name or drawing.file.name,
                "file_type": drawing.file_type,
                "status": drawing.status,
                "created_at": (
                    drawing.created_at.isoformat() if drawing.created_at else None
                ),
                "processed_at": (
                    drawing.processed_at.isoformat() if drawing.processed_at else None
                ),
                "calculations": [],
            }

            calculations = (
                Calculation.objects
                .filter(drawing=drawing)
                .prefetch_related("items__material")
            )

            for calculation in calculations:

                calculation_data = {
                    "id": calculation.id,
                    "status": calculation.status,
                    "total_area": (
                        str(calculation.total_area)
                        if calculation.total_area is not None
                        else None
                    ),
                    "total_wall_length": (
                        str(calculation.total_wall_length)
                        if calculation.total_wall_length is not None
                        else None
                    ),
                    "total_material_cost": str(calculation.total_material_cost),
                    "currency": calculation.currency,
                    "error_message": calculation.error_message,
                    "created_at": (
                        calculation.created_at.isoformat()
                        if calculation.created_at
                        else None
                    ),
                    "updated_at": (
                        calculation.updated_at.isoformat()
                        if calculation.updated_at
                        else None
                    ),
                    "items": [],
                }

                for item in calculation.items.all():
                    calculation_data["items"].append(
                        {
                            "material": item.material.name,
                            "quantity": str(item.quantity),
                            "unit": item.unit,
                            "unit_price": str(item.unit_price),
                            "total_price": str(item.total_price),
                        }
                    )

                drawing_data["calculations"].append(calculation_data)

            project_data["drawings"].append(drawing_data)

        context["projects"].append(project_data)

    return context


# ============================================================
# COPILOT PAGE
# ============================================================

@login_required(login_url="login")
def copilot_page(request):
    projects = Project.objects.filter(user=request.user)
    return render(
        request,
        "copilot.html",
        {
            "projects": projects,
            "projects_count": projects.count(),
        },
    )


# ============================================================
# PUBLIC COPILOT API
# ============================================================

@require_POST
def copilot_public_chat_api(request):
    """
    Landing page uchun ochiq Copilot.
    Login talab qilmaydi, private context yuborilmaydi.
    """

    try:
        body = json.loads(request.body or "{}")
        message = str(body.get("message", "")).strip()
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Noto'g'ri so'rov."}, status=400)

    if not message:
        return JsonResponse({"error": "Savol kiriting."}, status=400)

    if len(message) > 4000:
        return JsonResponse({"error": "Savol juda uzun."}, status=400)

    try:
        answer = _call_openrouter(message)
    except RuntimeError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    return JsonResponse({"response": answer})


# ============================================================
# PRIVATE COPILOT API
# ============================================================

@login_required(login_url="login")
@require_POST
def copilot_chat_api(request):
    """
    Private AI Copilot API.
    Foydalanuvchining shaxsiy loyiha ma'lumotlari kontekstga qo'shiladi.
    """

    try:
        body = json.loads(request.body or "{}")
        message = str(body.get("message", "")).strip()
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Noto'g'ri so'rov."}, status=400)

    if not message:
        return JsonResponse({"error": "Savol kiriting."}, status=400)

    if len(message) > 4000:
        return JsonResponse({"error": "Savol juda uzun."}, status=400)

    # --------------------------------------------------------
    # USER PRIVATE CONTEXT
    # --------------------------------------------------------

    private_context = _user_copilot_context(request.user)

    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    prompt = f"""
Siz BuildAI platformasining AI Copilot yordamchisisiz.

Siz foydalanuvchiga quyidagi ikki turdagi yordamni berasiz:

1. Umumiy savollar:
   - qurilish, loyiha, chizma, materiallar, smeta, hisob-kitob;
   - BuildAI tizimi, texnik va umumiy savollar.

2. Foydalanuvchining shaxsiy BuildAI ma'lumotlari:
   - loyihalari, chizmalari, hisob-kitoblari;
   - materiallari, narxlari, maydonlari, devor uzunliklari.

MUHIM MAXFIYLIK QOIDASI:

Quyidagi PRIVATE_BUILDAI_USER_CONTEXT faqat hozirgi
autentifikatsiyadan o'tgan foydalanuvchiga tegishli.

PRIVATE_CONTEXT ichida mavjud bo'lmagan ma'lumotni o'ylab topmang.

Agar kerakli ma'lumot context ichida bo'lmasa, buni ochiq ayting.

Agar savol private loyiha ma'lumotlariga aloqador bo'lmasa,
oddiy umumiy bilim asosida javob bering.

Javoblarni foydalanuvchiga qulay, tushunarli va tabiiy
o'zbek tilida bering.

PRIVATE_BUILDAI_USER_CONTEXT:

{json.dumps(private_context, ensure_ascii=False, default=str)}

USER_QUESTION:

{message}
""".strip()

    # --------------------------------------------------------
    # CALL OPENROUTER
    # --------------------------------------------------------

    try:
        answer = _call_openrouter(prompt)
    except RuntimeError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    return JsonResponse({"response": answer})
