import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-only-change-me")
# Safe by default: production must opt in explicitly, staging sets DEBUG=true
# in its env file so errors stay visible there.
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "rest_framework",
    "apps.accounts",
    "apps.analytics",
    "apps.catalog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = "en-us"
# Algeria runs on UTC+1 all year round (no daylight saving).
TIME_ZONE = "Africa/Algiers"
# The database stores the Algerian wall clock itself, so a row written at
# 15:10 is read back as 15:10 — not as 14:10 UTC.
USE_TZ = False
USE_I18N = True

STATIC_URL = os.getenv("STATIC_URL", "static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.accounts.authentication.CookieJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_COOKIE": "access",
    "AUTH_COOKIE_REFRESH": "refresh",
    "AUTH_COOKIE_HTTP_ONLY": True,
    # Over HTTP (IP + port access) browsers reject Secure cookies, so allow an
    # explicit override while keeping the safe default in production.
    "AUTH_COOKIE_SECURE": os.getenv("AUTH_COOKIE_SECURE", str(not DEBUG)).lower() == "true",
    "AUTH_COOKIE_SAMESITE": "Lax",
    "AUTH_COOKIE_PATH": "/",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Digi Store API",
    "DESCRIPTION": "Digital products storefront API with categories, products, packages, and customer credit.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
CORS_ALLOWED_ORIGINS += [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

UNFOLD = {
    "SITE_TITLE": "Digi Store",
    "SITE_HEADER": "Digi Store",
    "SITE_SUBHEADER": "Digital products",
    "SITE_SYMBOL": "storefront",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "DASHBOARD_CALLBACK": "config.dashboard.dashboard_callback",
    # The analytics page of the shop: the cards and the charts.
    "SITE_VIEWS": [
        (
            "analytics/",
            "analytics",
            "apps.analytics.admin_views.AnalyticsAdminView",
        ),
    ],
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Shop"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Categories"),
                        "icon": "category",
                        "link": reverse_lazy("admin:catalog_category_changelist"),
                    },
                    {
                        "title": _("Products"),
                        "icon": "inventory_2",
                        "link": reverse_lazy("admin:catalog_product_changelist"),
                    },
                    {
                        "title": _("Packages"),
                        "icon": "package_2",
                        "link": reverse_lazy("admin:catalog_package_changelist"),
                    },
                    {
                        "title": _("Package groups"),
                        "icon": "layers",
                        "link": reverse_lazy("admin:catalog_packagegroup_changelist"),
                    },
                    {
                        "title": _("Package codes"),
                        "icon": "qr_code_2",
                        "link": reverse_lazy("admin:catalog_packagecode_changelist"),
                    },
                    {
                        "title": _("Promotions"),
                        "icon": "sell",
                        "link": reverse_lazy("admin:catalog_promotion_changelist"),
                    },
                ],
            },
            {
                "title": _("Customers"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                    {
                        "title": _("Orders"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:accounts_order_changelist"),
                    },
                    {
                        "title": _("Transactions"),
                        "icon": "swap_horiz",
                        "link": reverse_lazy("admin:accounts_transaction_changelist"),
                    },
                    {
                        "title": _("Credits"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:accounts_credit_changelist"),
                    },
                    {
                        "title": _("Notifications"),
                        "icon": "notifications",
                        "link": reverse_lazy("admin:accounts_notification_changelist"),
                    },
                    {
                        "title": _("Order reports"),
                        "icon": "report",
                        "link": reverse_lazy("admin:accounts_orderreport_changelist"),
                    },
                ],
            },
            {
                "title": _("Locations"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Regions"),
                        "icon": "public",
                        "link": reverse_lazy("admin:accounts_region_changelist"),
                    },
                    {
                        "title": _("Wilayas"),
                        "icon": "location_city",
                        "link": reverse_lazy("admin:accounts_wilaya_changelist"),
                    },
                    {
                        "title": _("Dairas"),
                        "icon": "map",
                        "link": reverse_lazy("admin:accounts_daira_changelist"),
                    },
                ],
            },
            {
                "title": _("Analytics"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Overview"),
                        "icon": "insights",
                        "link": reverse_lazy("admin:analytics"),
                    },
                    {
                        "title": _("Analytics runs"),
                        "icon": "history",
                        "link": reverse_lazy("admin:analytics_analyticsrun_changelist"),
                    },
                    {
                        "title": _("Sales aggregates"),
                        "icon": "bar_chart",
                        "link": reverse_lazy("admin:analytics_salesaggregate_changelist"),
                    },
                ],
            },
            {
                "title": _("Authentication and Authorization"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Groups"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },
}
