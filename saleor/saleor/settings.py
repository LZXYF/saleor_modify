import ast
import os.path

import dj_database_url
import dj_email_url
import django_cache_url
from django.contrib.messages import constants as messages
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django_prices.templatetags.prices_i18n import get_currency_fraction

from . import __version__


def get_list(text):
    return [item.strip() for item in text.split(",")]


def get_bool_from_env(name, default_value):
    if name in os.environ:
        value = os.environ[name]
        try:
            return ast.literal_eval(value)
        except ValueError as e:
            raise ValueError("{} is an invalid value for {}".format(value, name)) from e
    return default_value


DEBUG = get_bool_from_env("DEBUG", True)

SITE_ID = 1

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

ROOT_URLCONF = "saleor.urls"

WSGI_APPLICATION = "saleor.wsgi.application"

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

INTERNAL_IPS = get_list(os.environ.get("INTERNAL_IPS", "127.0.0.1"))

# Some cloud providers (Heroku) export REDIS_URL variable instead of CACHE_URL
REDIS_URL = os.environ.get("REDIS_URL")
if REDIS_URL:
    CACHE_URL = os.environ.setdefault("CACHE_URL", REDIS_URL)
CACHES = {"default": django_cache_url.config()}

DATABASES = {
    "default": dj_database_url.config(
        default="postgres://simm:simm@localhost:5432/kkk", conn_max_age=600
    )
}


TIME_ZONE = "America/Chicago"
LANGUAGE_CODE = "en"
LANGUAGES = [
    ("ar", _("Arabic")),
    ("az", _("Azerbaijani")),
    ("bg", _("Bulgarian")),
    ("bn", _("Bengali")),
    ("ca", _("Catalan")),
    ("cs", _("Czech")),
    ("da", _("Danish")),
    ("de", _("German")),
    ("en", _("English")),
    ("es", _("Spanish")),
    ("es-co", _("Colombian Spanish")),
    ("et", _("Estonian")),
    ("fa", _("Persian")),
    ("fr", _("French")),
    ("hi", _("Hindi")),
    ("hu", _("Hungarian")),
    ("hy", _("Armenian")),
    ("id", _("Indonesian")),
    ("is", _("Icelandic")),
    ("it", _("Italian")),
    ("ja", _("Japanese")),
    ("ko", _("Korean")),
    ("lt", _("Lithuanian")),
    ("mn", _("Mongolian")),
    ("nb", _("Norwegian")),
    ("nl", _("Dutch")),
    ("pl", _("Polish")),
    ("pt", _("Portuguese")),
    ("pt-br", _("Brazilian Portuguese")),
    ("ro", _("Romanian")),
    ("ru", _("Russian")),
    ("sk", _("Slovak")),
    ("sq", _("Albanian")),
    ("sr", _("Serbian")),
    ("sw", _("Swahili")),
    ("sv", _("Swedish")),
    ("th", _("Thai")),
    ("tr", _("Turkish")),
    ("uk", _("Ukrainian")),
    ("vi", _("Vietnamese")),
    ("zh-hans", _("Simplified Chinese")),
    ("zh-hant", _("Traditional Chinese")),
]
LOCALE_PATHS = [os.path.join(PROJECT_ROOT, "locale")]
USE_I18N = True
USE_L10N = True
USE_TZ = True

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

EMAIL_URL = os.environ.get("EMAIL_URL")
SENDGRID_USERNAME = os.environ.get("SENDGRID_USERNAME")
SENDGRID_PASSWORD = os.environ.get("SENDGRID_PASSWORD")
if not EMAIL_URL and SENDGRID_USERNAME and SENDGRID_PASSWORD:
    EMAIL_URL = "smtp://%s:%s@smtp.sendgrid.net:587/?tls=False" % (
        SENDGRID_USERNAME,
        SENDGRID_PASSWORD,
    )
email_config = dj_email_url.parse(EMAIL_URL or "console://")

EMAIL_FILE_PATH = email_config["EMAIL_FILE_PATH"]
EMAIL_HOST_USER = email_config["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = email_config["EMAIL_HOST_PASSWORD"]
EMAIL_HOST = email_config["EMAIL_HOST"]
EMAIL_PORT = email_config["EMAIL_PORT"]
EMAIL_BACKEND = email_config["EMAIL_BACKEND"]
EMAIL_USE_TLS = email_config["EMAIL_USE_TLS"]
EMAIL_USE_SSL = email_config["EMAIL_USE_SSL"]

ENABLE_SSL = get_bool_from_env("ENABLE_SSL", False)

if ENABLE_SSL:
    SECURE_SSL_REDIRECT = not DEBUG

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
ORDER_FROM_EMAIL = os.getenv("ORDER_FROM_EMAIL", DEFAULT_FROM_EMAIL)

MEDIA_ROOT = os.path.join(PROJECT_ROOT, "media")
MEDIA_URL = os.environ.get("MEDIA_URL", "/media/")

STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")
STATIC_URL = os.environ.get("STATIC_URL", "/static/")
STATICFILES_DIRS = [
    ("assets", os.path.join(PROJECT_ROOT, "saleor", "static", "assets")),
    ("favicons", os.path.join(PROJECT_ROOT, "saleor", "static", "favicons")),
    ("images", os.path.join(PROJECT_ROOT, "saleor", "static", "images")),
    ("marvinjs", os.path.join(PROJECT_ROOT, "saleor", "static", "marvinjs")),
    (
        "dashboard/images",
        os.path.join(PROJECT_ROOT, "saleor", "static", "dashboard", "images"),
    ),
    # 二维码图片位置
    ("imgs", os.path.join(PROJECT_ROOT, "saleor", "static", "imgs")),
]
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

context_processors = [
    "django.contrib.auth.context_processors.auth",
    "django.template.context_processors.debug",
    "django.template.context_processors.i18n",
    "django.template.context_processors.media",
    "django.template.context_processors.static",
    "django.template.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.template.context_processors.request",
    "saleor.core.context_processors.default_currency",
    "saleor.checkout.context_processors.checkout_counter",
    "saleor.core.context_processors.search_enabled",
    "saleor.site.context_processors.site",
    "social_django.context_processors.backends",
    "social_django.context_processors.login_redirect",
]

loaders = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

if not DEBUG:
    loaders = [("django.template.loaders.cached.Loader", loaders)]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(PROJECT_ROOT, "templates")],
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": context_processors,
            "loaders": loaders,
            "string_if_invalid": '<< MISSING VARIABLE "%s" >>' if DEBUG else "",
        },
    }
]

# Make this unique, and don't share it with anybody.
SECRET_KEY = '123445dfdfdfdscxc'
PREFIX_DEFAULT_LOCALE=False
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # "django.middleware.locale.LocaleMiddleware",
    "django_babel.middleware.LocaleMiddleware",
    "saleor.core.middleware.discounts",
    "saleor.core.middleware.google_analytics",
    "saleor.core.middleware.country",
    "saleor.core.middleware.currency",
    "saleor.core.middleware.site",
    "saleor.core.middleware.taxes",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "impersonate.middleware.ImpersonateMiddleware",
    "saleor.graphql.middleware.jwt_middleware",
]

INSTALLED_APPS = [
    # External apps that need to go before django's
    "storages",
    # Django modules
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.contrib.auth",
    "django.contrib.postgres",
    "django.forms",
    # Local apps
    "saleor.account",
    "saleor.discount",
    "saleor.giftcard",
    "saleor.product",
    "saleor.checkout",
    "saleor.core",
    "saleor.graphql",
    "saleor.menu",
    "saleor.order",
    "saleor.dashboard",
    "saleor.seo",
    "saleor.shipping",
    "saleor.search",
    "saleor.site",
    "saleor.data_feeds",
    "saleor.page",
    "saleor.payment",
    # External apps
    "versatileimagefield",
    "django_babel",
    "bootstrap4",
    "django_measurement",
    "django_prices",
    "django_prices_openexchangerates",
    "django_prices_vatlayer",
    "graphene_django",
    "mptt",
    "webpack_loader",
    "social_django",
    "django_countries",
    "django_filters",
    "impersonate",
    "phonenumber_field",
    "captcha",
    #"saleor.alipay"
]


ENABLE_DEBUG_TOOLBAR = get_bool_from_env("ENABLE_DEBUG_TOOLBAR", False)
if ENABLE_DEBUG_TOOLBAR:
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
    INSTALLED_APPS.append("debug_toolbar")
    DEBUG_TOOLBAR_PANELS = [
        # adds a request history to the debug toolbar
        "ddt_request_history.panels.request_history.RequestHistoryPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ]
    DEBUG_TOOLBAR_CONFIG = {"RESULTS_CACHE_SIZE": 100}

ENABLE_SILK = get_bool_from_env("ENABLE_SILK", False)
if ENABLE_SILK:
    MIDDLEWARE.insert(0, "silk.middleware.SilkyMiddleware")
    INSTALLED_APPS.append("silk")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {"level": "INFO", "handlers": ["console"]},
    "formatters": {
        "verbose": {
            "format": (
                "%(levelname)s %(name)s %(message)s [PID:%(process)d:%(threadName)s]"
            )
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "mail_admins"],
            "level": "INFO",
            "propagate": True,
        },
        "django.server": {"handlers": ["console"], "level": "INFO", "propagate": True},
        "saleor": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
    },
}

AUTH_USER_MODEL = "account.User"

LOGIN_URL = "/account/login/"

DEFAULT_COUNTRY = os.environ.get("DEFAULT_COUNTRY", "US")
DEFAULT_CURRENCY = os.environ.get("DEFAULT_CURRENCY", "USD")
DEFAULT_DECIMAL_PLACES = get_currency_fraction(DEFAULT_CURRENCY)
DEFAULT_MAX_DIGITS = 12
AVAILABLE_CURRENCIES = [DEFAULT_CURRENCY]
COUNTRIES_OVERRIDE = {
    "EU": pgettext_lazy(
        "Name of political and economical union of european countries", "European Union"
    )
}

OPENEXCHANGERATES_API_KEY = os.environ.get("OPENEXCHANGERATES_API_KEY")

# VAT configuration
# Enabling vat requires valid vatlayer access key.
# If you are subscribed to a paid vatlayer plan, you can enable HTTPS.
VATLAYER_ACCESS_KEY = os.environ.get("VATLAYER_ACCESS_KEY")
VATLAYER_USE_HTTPS = get_bool_from_env("VATLAYER_USE_HTTPS", False)

# Avatax supports two ways of log in - username:password or account:license
AVATAX_USERNAME_OR_ACCOUNT = os.environ.get("AVATAX_USERNAME_OR_ACCOUNT")
AVATAX_PASSWORD_OR_LICENSE = os.environ.get("AVATAX_PASSWORD_OR_LICENSE")
AVATAX_USE_SANDBOX = os.environ.get("AVATAX_USE_SANDBOX", DEBUG)
AVATAX_COMPANY_NAME = os.environ.get("AVATAX_COMPANY_NAME", "DEFAULT")
AVATAX_AUTOCOMMIT = os.environ.get("AVATAX_AUTOCOMMIT", False)

ACCOUNT_ACTIVATION_DAYS = 3

LOGIN_REDIRECT_URL = "home"

GOOGLE_ANALYTICS_TRACKING_ID = os.environ.get("GOOGLE_ANALYTICS_TRACKING_ID")


def get_host():
    from django.contrib.sites.models import Site

    return Site.objects.get_current().domain


PAYMENT_HOST = get_host

PAYMENT_MODEL = "order.Payment"

SESSION_SERIALIZER = "django.contrib.sessions.serializers.JSONSerializer"

# Do not use cached session if locmem cache backend is used but fallback to use
# default django.contrib.sessions.backends.db instead
if not CACHES["default"]["BACKEND"].endswith("LocMemCache"):
    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

MESSAGE_TAGS = {messages.ERROR: "danger"}

LOW_STOCK_THRESHOLD = 10
MAX_CHECKOUT_LINE_QUANTITY = int(os.environ.get("MAX_CHECKOUT_LINE_QUANTITY", 50))

PAGINATE_BY = 16
DASHBOARD_PAGINATE_BY = 30
DASHBOARD_SEARCH_LIMIT = 5

bootstrap4 = {
    "set_placeholder": False,
    "set_required": False,
    "success_css_class": "",
    "form_renderers": {"default": "saleor.core.utils.form_renderer.FormRenderer"},
}

TEST_RUNNER = "tests.runner.PytestTestRunner"

ALLOWED_HOSTS = get_list(os.environ.get("ALLOWED_HOSTS", "*,localhost,127.0.0.1"))
ALLOWED_GRAPHQL_ORIGINS = os.environ.get("ALLOWED_GRAPHQL_ORIGINS", "*")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Amazon S3 configuration
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_LOCATION = os.environ.get("AWS_LOCATION", "")
AWS_MEDIA_BUCKET_NAME = os.environ.get("AWS_MEDIA_BUCKET_NAME")
AWS_MEDIA_CUSTOM_DOMAIN = os.environ.get("AWS_MEDIA_CUSTOM_DOMAIN")
AWS_QUERYSTRING_AUTH = get_bool_from_env("AWS_QUERYSTRING_AUTH", False)
AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_STATIC_CUSTOM_DOMAIN")
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", None)
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_DEFAULT_ACL = os.environ.get("AWS_DEFAULT_ACL", None)

# Google Cloud Storage configuration
GS_PROJECT_ID = os.environ.get("GS_PROJECT_ID")
GS_STORAGE_BUCKET_NAME = os.environ.get("GS_STORAGE_BUCKET_NAME")
GS_MEDIA_BUCKET_NAME = os.environ.get("GS_MEDIA_BUCKET_NAME")
GS_AUTO_CREATE_BUCKET = get_bool_from_env("GS_AUTO_CREATE_BUCKET", False)

# If GOOGLE_APPLICATION_CREDENTIALS is set there is no need to load OAuth token
# See https://django-storages.readthedocs.io/en/latest/backends/gcloud.html
if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
    GS_CREDENTIALS = os.environ.get("GS_CREDENTIALS")

if AWS_STORAGE_BUCKET_NAME:
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
elif GS_STORAGE_BUCKET_NAME:
    STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"

if AWS_MEDIA_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = "saleor.core.storages.S3MediaStorage"
    THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE
elif GS_MEDIA_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = "saleor.core.storages.GCSMediaStorage"
    THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    "products": [
        ("product_gallery", "thumbnail__540x540"),
        ("product_gallery_2x", "thumbnail__1080x1080"),
        ("product_small", "thumbnail__60x60"),
        ("product_small_2x", "thumbnail__120x120"),
        ("product_list", "thumbnail__255x255"),
        ("product_list_2x", "thumbnail__510x510"),
    ],
    "background_images": [("header_image", "thumbnail__1080x440")],
    "user_avatars": [("default", "thumbnail__445x445")],
}

VERSATILEIMAGEFIELD_SETTINGS = {
    # Images should be pre-generated on Production environment
    "create_images_on_demand": get_bool_from_env("CREATE_IMAGES_ON_DEMAND", DEBUG)
}

PLACEHOLDER_IMAGES = {
    60: "images/placeholder60x60.png",
    120: "images/placeholder120x120.png",
    255: "images/placeholder255x255.png",
    540: "images/placeholder540x540.png",
    1080: "images/placeholder1080x1080.png",
}

DEFAULT_PLACEHOLDER = "images/placeholder255x255.png"

WEBPACK_LOADER = {
    "DEFAULT": {
        "CACHE": not DEBUG,
        "BUNDLE_DIR_NAME": "assets/",
        "STATS_FILE": os.path.join(PROJECT_ROOT, "webpack-bundle.json"),
        "POLL_INTERVAL": 0.1,
        "IGNORE": [r".+\.hot-update\.js", r".+\.map"],
    }
}


LOGOUT_ON_PASSWORD_CHANGE = False

# SEARCH CONFIGURATION
DB_SEARCH_ENABLED = True

# support deployment-dependant elastic enviroment variable
ES_URL = (
    os.environ.get("ELASTICSEARCH_URL")
    or os.environ.get("SEARCHBOX_URL")
    or os.environ.get("BONSAI_URL")
)

ENABLE_SEARCH = bool(ES_URL) or DB_SEARCH_ENABLED  # global search disabling

SEARCH_BACKEND = "saleor.search.backends.postgresql"

if ES_URL:
    SEARCH_BACKEND = "saleor.search.backends.elasticsearch"
    INSTALLED_APPS.append("django_elasticsearch_dsl")
    ELASTICSEARCH_DSL = {"default": {"hosts": ES_URL}}

AUTHENTICATION_BACKENDS = [
    "saleor.account.backends.facebook.CustomFacebookOAuth2",
    "saleor.account.backends.google.CustomGoogleOAuth2",
    "graphql_jwt.backends.JSONWebTokenBackend",
    "django.contrib.auth.backends.ModelBackend",
]

SOCIAL_AUTH_PIPELINE = [
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
]

SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_USER_MODEL = AUTH_USER_MODEL
SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {"fields": "id, email"}
# As per March 2018, Facebook requires all traffic to go through HTTPS only
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

# CELERY SETTINGS
CELERY_BROKER_URL = (
    os.environ.get("CELERY_BROKER_URL", os.environ.get("CLOUDAMQP_URL")) or ""
)
CELERY_TASK_ALWAYS_EAGER = not CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", None)

# Impersonate module settings
IMPERSONATE = {
    "URI_EXCLUSIONS": [r"^dashboard/"],
    "CUSTOM_USER_QUERYSET": "saleor.account.impersonate.get_impersonatable_users",  # noqa
    "USE_HTTP_REFERER": True,
    "CUSTOM_ALLOW": "saleor.account.impersonate.can_impersonate",
}


# Rich-text editor
ALLOWED_TAGS = [
    "a",
    "b",
    "blockquote",
    "br",
    "em",
    "h2",
    "h3",
    "i",
    "img",
    "li",
    "ol",
    "p",
    "strong",
    "ul",
]
ALLOWED_ATTRIBUTES = {"*": ["align", "style"], "a": ["href", "title"], "img": ["src"]}
ALLOWED_STYLES = ["text-align"]


# Slugs for menus precreated in Django migrations
DEFAULT_MENUS = {"top_menu_name": "navbar", "bottom_menu_name": "footer"}

# This enable the new 'No Captcha reCaptcha' version (the simple checkbox)
# instead of the old (deprecated) one. For more information see:
#   https://github.com/praekelt/django-recaptcha/blob/34af16ba1e/README.rst
NOCAPTCHA = True

# Set Google's reCaptcha keys
RECAPTCHA_PUBLIC_KEY = os.environ.get("RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = os.environ.get("RECAPTCHA_PRIVATE_KEY")


#  Sentry
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    INSTALLED_APPS.append("raven.contrib.django.raven_compat")
    RAVEN_CONFIG = {"dsn": SENTRY_DSN, "release": __version__}


SERIALIZATION_MODULES = {"json": "saleor.core.utils.json_serializer"}


DUMMY = "dummy"
BRAINTREE = "braintree"
RAZORPAY = "razorpay"
STRIPE = "stripe"

CHECKOUT_PAYMENT_GATEWAYS = {
    DUMMY: pgettext_lazy("Payment method name", "Dummy gateway")
}

PAYMENT_GATEWAYS = {
    DUMMY: {
        "module": "saleor.payment.gateways.dummy",
        "config": {
            "auto_capture": True,
            "store_card": False,
            "connection_params": {},
            "template_path": "order/payment/dummy.html",
        },
    },
    BRAINTREE: {
        "module": "saleor.payment.gateways.braintree",
        "config": {
            "auto_capture": get_bool_from_env("BRAINTREE_AUTO_CAPTURE", True),
            "store_card": get_bool_from_env("BRAINTREE_STORE_CARD", False),
            "template_path": "order/payment/braintree.html",
            "connection_params": {
                "sandbox_mode": get_bool_from_env("BRAINTREE_SANDBOX_MODE", True),
                "merchant_id": os.environ.get("BRAINTREE_MERCHANT_ID"),
                "public_key": os.environ.get("BRAINTREE_PUBLIC_KEY"),
                "private_key": os.environ.get("BRAINTREE_PRIVATE_KEY"),
            },
        },
    },
    RAZORPAY: {
        "module": "saleor.payment.gateways.razorpay",
        "config": {
            "store_card": get_bool_from_env("RAZORPAY_STORE_CARD", False),
            "auto_capture": get_bool_from_env("RAZORPAY_AUTO_CAPTURE", None),
            "template_path": "order/payment/razorpay.html",
            "connection_params": {
                "public_key": os.environ.get("RAZORPAY_PUBLIC_KEY"),
                "secret_key": os.environ.get("RAZORPAY_SECRET_KEY"),
                "prefill": get_bool_from_env("RAZORPAY_PREFILL", True),
                "store_name": os.environ.get("RAZORPAY_STORE_NAME"),
                "store_image": os.environ.get("RAZORPAY_STORE_IMAGE"),
            },
        },
    },
    STRIPE: {
        "module": "saleor.payment.gateways.stripe",
        "config": {
            "store_card": get_bool_from_env("STRIPE_STORE_CARD", False),
            "auto_capture": get_bool_from_env("STRIPE_AUTO_CAPTURE", True),
            "template_path": "order/payment/stripe.html",
            "connection_params": {
                "public_key": os.environ.get("STRIPE_PUBLIC_KEY"),
                "secret_key": os.environ.get("STRIPE_SECRET_KEY"),
                "store_name": os.environ.get("STRIPE_STORE_NAME", "Saleor"),
                "remember_me": os.environ.get("STRIPE_REMEMBER_ME", True),
                "locale": os.environ.get("STRIPE_LOCALE", "auto"),
                "enable_billing_address": os.environ.get(
                    "STRIPE_ENABLE_BILLING_ADDRESS", False
                ),
                "enable_shipping_address": os.environ.get(
                    "STRIPE_ENABLE_SHIPPING_ADDRESS", False
                ),
            },
        },
    },
}

GRAPHENE = {
    "RELAY_CONNECTION_ENFORCE_FIRST_OR_LAST": True,
    "RELAY_CONNECTION_MAX_LIMIT": 100,
}

# 支付宝参数配置
class AliPayConfig(object):

    addressIp = "211.64.38.90:8008"


    # 正式启用时需要重新配置app_id ，merchant_private_key_path ，alipay_public_key_path
    app_id = "2016092700607535"  # APPID  沙箱应用

    # 支付完成后支付宝向这里发送一个post请求，如果识别为局域网ip，支付宝找不到，alipay_result（）接受不到这个请求
    notify_url = "http://"+ addressIp +"/pays/alipay_result"

    # 支付完成后跳转的地址
    return_url = "http://" + addressIp + "/pays/alipay_result"
    # 应用私钥
    merchant_private_key_path = os.path.join(PROJECT_ROOT, "saleor/alipay/keys/app_private_key.pem")
    # 支付宝公钥
    alipay_public_key_path = os.path.join(PROJECT_ROOT, "saleor/alipay/keys/alipay_public_key.pem")  # 验证支付宝回传消息使用

# 微信支付参数配置
class WxPayConfig(object):
    addressIp = "211.64.38.90:8008"
    
    # 微信的证书
    wx_apiclient_cert_path = os.path.join(PROJECT_ROOT,"saleor/alipay/keys/wx/apiclient_cert.pem")
    wx_apiclient_key_path = os.path.join(PROJECT_ROOT,"saleor/alipay/keys/wx/apiclient_key.pem")
    # 微信商户密钥，签名验证用
    wx_mch_key = "alphamalizhaojunalphamalizhaojun"
    # 微信支付异步回调地址
    wx_notify_url = "http://" + addressIp + "/pays/wxpay_result"
    wx_mch_id = "1571129241"
    wx_app_id = "ww58ea0a6e86779b7c"



