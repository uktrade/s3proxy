import os
import environ

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Read environment variables using `django-environ`, use `.env` if it exists
env = environ.Env()
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    env.read_env(env_file)

# Set required configuration from environment
APP_ENV = env.str("APP_ENV", "local")

AUTHBROKER_URL = env("AUTHBROKER_URL")
AUTHBROKER_CLIENT_ID = env("AUTHBROKER_CLIENT_ID")
AUTHBROKER_CLIENT_SECRET = env("AUTHBROKER_CLIENT_SECRET")

DEBUG = env.bool("DJANGO_DEBUG", False)

SECRET_KEY = env("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = ["*"]

VCAP_SERVICES = env.json("VCAP_SERVICES", {})

if "postgres" in VCAP_SERVICES:
    DATABASE_URL = VCAP_SERVICES["postgres"][0]["credentials"]["uri"]
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

DATABASES = {"default": env.db()}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "file_proxy",
    "user",
    "authbroker_client",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "authbroker_client.middleware.ProtectAllViewsMiddleware",
]

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"

AUTHENTICATION_BACKENDS = [
    "user.backends.CustomAuthBrokerBackend",
]

# AWS
if "aws-s3-bucket" in VCAP_SERVICES:
    app_bucket_creds = VCAP_SERVICES["aws-s3-bucket"][0]["credentials"]
    AWS_REGION = app_bucket_creds["aws_region"]
    AWS_DEFAULT_REGION = app_bucket_creds["aws_region"]
    AWS_STORAGE_BUCKET_NAME = app_bucket_creds["bucket_name"]
    AWS_ACCESS_KEY_ID = app_bucket_creds["aws_access_key_id"]
    AWS_SECRET_ACCESS_KEY = app_bucket_creds["aws_secret_access_key"]
else:
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_REGION = env("AWS_REGION", default="eu-west-2")
    AWS_DEFAULT_REGION = env("AWS_REGION", default="eu-west-2")
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Chunk size
CHUNK_SIZE = env.int("CHUNK_SIZE", 5120)
