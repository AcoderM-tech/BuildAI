import os
import dj_database_url
import urllib.parse
from pathlib import Path
from decouple import config

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Core settings
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost:8000').split(',')

# Applications configuration
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
    
    # Django-allauth talab qiladigan ilovalar
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database Setup
raw_db_url = config('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")

if raw_db_url.startswith("postgresql://") or raw_db_url.startswith("postgres://"):
    try:
        base_url, _, query_params = raw_db_url.partition("?")
        scheme, _, rest = base_url.partition("://")
        auth_part, _, host_part = rest.rpartition("@")
        if auth_part:
            username, _, password = auth_part.partition(":")
            if password:
                encoded_password = urllib.parse.quote_plus(password)
                reconstructed_url = f"{scheme}://{username}:{encoded_password}@{host_part}"
                if query_params:
                    reconstructed_url = f"{reconstructed_url}?{query_params}"
                raw_db_url = reconstructed_url
    except Exception:
        pass

DATABASES = {
    'default': dj_database_url.config(
        default=raw_db_url,
        conn_max_age=600,
    )
}

# Passwords validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Localization
LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

# Static & Media Configuration
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Production security configurations
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Redirects URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'landing_page'

# Django-allauth Core & Social connection configurations
SITE_ID = 2

ACCOUNT_AUTHENTICATION_METHOD = 'email'       # Avtorizatsiya faqat email orqali amalga oshadi
ACCOUNT_EMAIL_REQUIRED = True                 # Email ro'yxatdan o'tishda majburiy
ACCOUNT_USERNAME_REQUIRED = False             # Foydalanuvchidan qo'shimcha username so'ralmaydi
ACCOUNT_UNIQUE_EMAIL = True                   # Har bir email tizimda takrorlanmas bo'lishi shart
ACCOUNT_EMAIL_VERIFICATION = 'none'           # Sinov yoki dastlabki bosqichda email tasdiqlash xati o'chirilgan

# Kuchaytirilgan avtomatik ro'yxatdan o'tish (Sign-up oynasini to'liq chetlab o'tish)
SOCIALACCOUNT_AUTO_SIGNUP = True              
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True     # Bazada email bor bo'lsa, Google hisobni avtomatik bog'laydi

# Standart adapterlar va token siyosati
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_LOGIN_ON_GET = True

# Session saqlash sozlamalari
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = True

# Google OAuth Provayderi sozlamalari
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    },
}
