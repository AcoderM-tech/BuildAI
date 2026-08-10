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
    """
    BuildAI Landing Page.
    """
    return render(request, "landing.html")


# ============================================================
# ABOUT
# ============================================================

def about_page(request):
    """
    Haqimizda sahifasi.
    """
    return render(request, "about.html")


# ============================================================
# AUTH
# ============================================================

def login_page(request):
    """
    Login sahifasi.
    """

    if request.user.is_authenticated:
        return redirect("dashboard")

    form = AuthenticationForm(
        request,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())

        next_url = (
            request.POST.get("next")
            or request.GET.get("next")
        )

        return redirect(next_url or "dashboard")

    return render(
        request,
        "login.html",
        {
            "form": form,
        },
    )


def register_page(request):
    """
    Ro'yxatdan o'tish sahifasi.
    """

    if request.user.is_authenticated:
        return redirect("dashboard")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()

        login(request, user)

        messages.success(
            request,
            "Xush kelibsiz! Ro'yxatdan muvaffaqiyatli o'tdingiz.",
        )

        return redirect("dashboard")

    return render(
        request,
        "registr.html",
        {
            "form": form,
        },
    )


def logout_view(request):
    """
    Tizimdan chiqish.
    """

    logout(request)

    return redirect("landing_page")


# ============================================================
# DASHBOARD
# ============================================================

@login_required(login_url="login")
def dashboard_view(request):
    """
    Foydalanuvchining shaxsiy Dashboard'i.

    Muhim:
    Project faqat request.user bo'yicha olinadi.
    """

    projects = Project.objects.filter(
        user=request.user
    )

    context = {
        "projects": projects,
        "projects_count": projects.count(),
        "active_count": projects.filter(
            status="active"
        ).count(),
        "completed_count": projects.filter(
            status="completed"
        ).count(),
        "draft_count": projects.filter(
            status="draft"
        ).count(),
    }

    return render(
        request,
        "dashboard.html",
        context,
    )


# ============================================================
# COMING SOON
# ============================================================

@login_required
def coming_soon(request, module_slug=None):
    """
    Hali ishlab chiqilmagan modullar uchun
    umumiy Coming Soon sahifasi.
    """

    return render(
        request,
        "coming_soon.html",
    )


# ============================================================
# AI COPILOT WORKER
# ============================================================

COPILOT_WORKER_URL = config(
    "COPILOT_WORKER_URL",
    default=(
        "https://little-cloud-199e."
        "avazbekmexriddinov63.workers.dev"
    ),
)


def _call_copilot_worker(prompt):
    """
    BuildAI Copilot Cloudflare Worker bilan aloqa.

    Worker'ga faqat POST orqali JSON yuboriladi:

        {
            "prompt": "..."
        }

    Worker javobida quyidagi formatlardan birini
    qo'llab-quvvatlaymiz:

        {
            "response": "..."
        }

    yoki:

        {
            "answer": "..."
        }

    yoki:

        {
            "message": "..."
        }

    Xatolik bo'lsa haqiqiy sababni qaytaradi.
    """

    if not COPILOT_WORKER_URL:
        raise RuntimeError(
            "COPILOT_WORKER_URL sozlanmagan."
        )

    payload = json.dumps(
        {
            "prompt": prompt,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    worker_request = urllib.request.Request(
        COPILOT_WORKER_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            worker_request,
            timeout=45,
        ) as response:

            raw_response = (
                response
                .read()
                .decode("utf-8")
            )

    # --------------------------------------------------------
    # HTTP ERROR
    # --------------------------------------------------------

    except urllib.error.HTTPError as exc:

        try:
            error_body = (
                exc.read()
                .decode(
                    "utf-8",
                    errors="replace",
                )
            )

        except Exception:
            error_body = ""

        raise RuntimeError(
            f"AI Worker HTTP {exc.code}: "
            f"{error_body[:1000]}"
        ) from exc

    # --------------------------------------------------------
    # CONNECTION ERROR
    # --------------------------------------------------------

    except urllib.error.URLError as exc:

        reason = getattr(
            exc,
            "reason",
            "Noma'lum ulanish xatosi",
        )

        raise RuntimeError(
            f"AI Worker bilan ulanib bo'lmadi: "
            f"{reason}"
        ) from exc

    # --------------------------------------------------------
    # TIMEOUT
    # --------------------------------------------------------

    except TimeoutError as exc:

        raise RuntimeError(
            "AI Worker javob berish uchun "
            "ajratilgan vaqt ichida javob bermadi."
        ) from exc

    # --------------------------------------------------------
    # OTHER NETWORK ERROR
    # --------------------------------------------------------

    except Exception as exc:

        raise RuntimeError(
            f"AI Worker xatosi: {str(exc)}"
        ) from exc

    # --------------------------------------------------------
    # JSON RESPONSE
    # --------------------------------------------------------

    try:

        data = json.loads(
            raw_response
        )

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            "AI Worker JSON formatida javob "
            "qaytarmadi.\n\n"
            f"Worker javobi:\n"
            f"{raw_response[:1000]}"
        ) from exc

    # --------------------------------------------------------
    # RESPONSE FORMAT
    # --------------------------------------------------------

    if not isinstance(data, dict):

        raise RuntimeError(
            "AI Worker noto'g'ri formatdagi "
            "javob qaytardi."
        )

    # Asosiy format
    answer = data.get("response")

    # Alternativ format
    if not answer:
        answer = data.get("answer")

    # Yana bir alternativ
    if not answer:
        answer = data.get("message")

    # --------------------------------------------------------
    # WORKER ERROR
    # --------------------------------------------------------

    if not answer:

        error = data.get("error")

        if error:

            raise RuntimeError(
                str(error)
            )

        raise RuntimeError(
            "AI Worker javobida AI matni "
            "topilmadi.\n\n"
            f"Worker javobi:\n"
            f"{raw_response[:1000]}"
        )

    return str(answer)


# ============================================================
# PRIVATE USER CONTEXT
# ============================================================

def _user_copilot_context(user):
    """
    Faqat autentifikatsiyadan o'tgan foydalanuvchining
    ma'lumotlarini Copilot uchun tayyorlaydi.

    MUHIM:
    Bu yerda boshqa foydalanuvchilarning Project'lari
    hech qachon olinmaydi.
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

    # --------------------------------------------------------
    # PROJECTS
    # --------------------------------------------------------

    for project in projects:

        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "created_at": (
                project.created_at.isoformat()
                if project.created_at
                else None
            ),
            "updated_at": (
                project.updated_at.isoformat()
                if project.updated_at
                else None
            ),
            "drawings": [],
        }

        # ----------------------------------------------------
        # DRAWINGS
        # ----------------------------------------------------

        for drawing in project.drawings.all():

            drawing_data = {
                "id": drawing.id,
                "original_name": (
                    drawing.original_name
                    or drawing.file.name
                ),
                "file_type": drawing.file_type,
                "status": drawing.status,
                "created_at": (
                    drawing.created_at.isoformat()
                    if drawing.created_at
                    else None
                ),
                "processed_at": (
                    drawing.processed_at.isoformat()
                    if drawing.processed_at
                    else None
                ),
                "calculations": [],
            }

            # ------------------------------------------------
            # CALCULATIONS
            # ------------------------------------------------

            calculations = (
                Calculation.objects
                .filter(drawing=drawing)
                .prefetch_related(
                    "items__material"
                )
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
                        str(
                            calculation.total_wall_length
                        )
                        if calculation.total_wall_length
                        is not None
                        else None
                    ),
                    "total_material_cost": str(
                        calculation.total_material_cost
                    ),
                    "currency": calculation.currency,
                    "error_message": (
                        calculation.error_message
                    ),
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

                # --------------------------------------------
                # CALCULATION ITEMS
                # --------------------------------------------

                for item in calculation.items.all():

                    calculation_data[
                        "items"
                    ].append(
                        {
                            "material": (
                                item.material.name
                            ),
                            "quantity": str(
                                item.quantity
                            ),
                            "unit": item.unit,
                            "unit_price": str(
                                item.unit_price
                            ),
                            "total_price": str(
                                item.total_price
                            ),
                        }
                    )

                drawing_data[
                    "calculations"
                ].append(
                    calculation_data
                )

            project_data[
                "drawings"
            ].append(
                drawing_data
            )

        context[
            "projects"
        ].append(
            project_data
        )

    return context


# ============================================================
# COPILOT PAGE
# ============================================================

@login_required(login_url="login")
def copilot_page(request):
    """
    Private AI Copilot sahifasi.

    Foydalanuvchi faqat o'z loyihalarini ko'radi.
    """

    projects = Project.objects.filter(
        user=request.user
    )

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
    Landing page'dagi public Copilot.

    Bu endpoint:
    - login talab qilmaydi;
    - database context yubormaydi;
    - faqat umumiy savolga javob beradi;
    - foydalanuvchining private ma'lumotlarini Worker'ga yubormaydi.
    """

    try:

        body = json.loads(
            request.body or "{}"
        )

        message = str(
            body.get(
                "message",
                "",
            )
        ).strip()

    except (
        json.JSONDecodeError,
        TypeError,
    ):

        return JsonResponse(
            {
                "error": "Noto'g'ri so'rov."
            },
            status=400,
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not message:

        return JsonResponse(
            {
                "error": "Savol kiriting."
            },
            status=400,
        )

    if len(message) > 4000:

        return JsonResponse(
            {
                "error": "Savol juda uzun."
            },
            status=400,
        )

    # --------------------------------------------------------
    # WORKER
    # --------------------------------------------------------

    try:

        answer = _call_copilot_worker(
            message
        )

    except RuntimeError as exc:

        return JsonResponse(
            {
                "error": str(exc)
            },
            status=502,
        )

    return JsonResponse(
        {
            "response": answer
        }
    )


# ============================================================
# PRIVATE COPILOT API
# ============================================================

@login_required(login_url="login")
@require_POST
def copilot_chat_api(request):
    """
    Private AI Copilot API.

    Foydalanuvchi:
        - umumiy savollar berishi mumkin;
        - o'z loyihalari haqida so'rashi mumkin;
        - o'z chizmalari haqida so'rashi mumkin;
        - o'z hisob-kitoblari haqida so'rashi mumkin.

    Worker'ga boshqa foydalanuvchining ma'lumotlari
    hech qachon yuborilmaydi.
    """

    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

    try:

        body = json.loads(
            request.body or "{}"
        )

        message = str(
            body.get(
                "message",
                "",
            )
        ).strip()

    except (
        json.JSONDecodeError,
        TypeError,
    ):

        return JsonResponse(
            {
                "error": "Noto'g'ri so'rov."
            },
            status=400,
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not message:

        return JsonResponse(
            {
                "error": "Savol kiriting."
            },
            status=400,
        )

    if len(message) > 4000:

        return JsonResponse(
            {
                "error": "Savol juda uzun."
            },
            status=400,
        )

    # --------------------------------------------------------
    # USER PRIVATE CONTEXT
    # --------------------------------------------------------

    private_context = _user_copilot_context(
        request.user
    )

    # --------------------------------------------------------
    # COPILOT SYSTEM INSTRUCTION
    # --------------------------------------------------------

    prompt = f"""
Siz BuildAI platformasining AI Copilot yordamchisisiz.

Siz foydalanuvchiga quyidagi ikki turdagi yordamni berasiz:

1. Umumiy savollar:
   - qurilish;
   - loyiha;
   - chizma;
   - materiallar;
   - smeta;
   - hisob-kitob;
   - BuildAI tizimi;
   - texnik va umumiy savollar.

2. Foydalanuvchining shaxsiy BuildAI ma'lumotlari:
   - loyihalari;
   - chizmalari;
   - hisob-kitoblari;
   - materiallari;
   - narxlari;
   - maydonlari;
   - devor uzunliklari.

MUHIM MAXFIYLIK QOIDASI:

Quyidagi PRIVATE_BUILDAI_USER_CONTEXT faqat hozirgi
autentifikatsiyadan o'tgan foydalanuvchiga tegishli.

Ushbu ma'lumotlarni boshqa foydalanuvchiga tegishli deb
qabul qilmang.

PRIVATE_CONTEXT ichida mavjud bo'lmagan ma'lumotni
o'ylab topmang.

Agar foydalanuvchi o'z loyihasi haqida so'rasa,
faqat PRIVATE_BUILDAI_USER_CONTEXT ichidagi ma'lumotlardan
foydalaning.

Agar kerakli ma'lumot context ichida bo'lmasa,
buni ochiq ayting.

Agar savol private loyiha ma'lumotlariga aloqador bo'lmasa,
oddiy umumiy bilim asosida javob bering.

Javoblarni foydalanuvchiga qulay, tushunarli va tabiiy
o'zbek tilida bering.

Keraksiz texnik tafsilotlarni aytmang.

PRIVATE_BUILDAI_USER_CONTEXT:

{json.dumps(
    private_context,
    ensure_ascii=False,
    default=str,
)}

USER_QUESTION:

{message}
""".strip()

    # --------------------------------------------------------
    # CALL WORKER
    # --------------------------------------------------------

    try:

        answer = _call_copilot_worker(
            prompt
        )

    except RuntimeError as exc:

        return JsonResponse(
            {
                "error": str(exc)
            },
            status=502,
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return JsonResponse(
        {
            "response": answer
        }
    )