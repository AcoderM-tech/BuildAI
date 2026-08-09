"""
URL configuration for config project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from main import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('admin/', admin.site.urls),
    path('about/', views.about_page, name='about'),

    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Google orqali kirish (django-allauth) — "Google orqali kirish"
    # tugmasi shu ilova orqali ishlaydi.
    path('accounts/', include('allauth.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)