"""CONFIG > settings.py"""

import os
from pathlib import Path

try:
    from .local_settings import (
        SECRET_KEY,
        DEBUG,
        ALLOWED_HOSTS,

        STATIC_DIR,
        STATICFILES_DIR,

        FTPSERVER_MASQUERADE_ADDRESS,
        FTPSERVER_PASSIVE_PORTS,

        AWS_ACCESS_KEY_ID,
        AWS_SECRET_ACCESS_KEY,
        AWS_STORAGE_BUCKET_NAME,
        AWS_S3_REGION_NAME,
        AWS_LOCATION,
    )
except Exception:
    AWS_ACCESS_KEY_ID = None
    AWS_SECRET_ACCESS_KEY = None
    AWS_STORAGE_BUCKET_NAME = None
    AWS_S3_REGION_NAME = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

SECRET_KEY = SECRET_KEY
DEBUG = DEBUG
ALLOWED_HOSTS = ALLOWED_HOSTS

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_ftpserver',
    # Add storages to support S3-backed media storage
    'storages',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'CONFIG.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'CONFIG.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = STATIC_DIR
STATICFILES_DIRS = [STATICFILES_DIR]


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# MEDIA / STORAGE -------------------------------------------------------------

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

if AWS_STORAGE_BUCKET_NAME:
    # Use S3-backed storage for media
    DEFAULT_FILE_STORAGE = "CONFIG.storages.MediaStorage"
    AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY
    AWS_STORAGE_BUCKET_NAME = AWS_STORAGE_BUCKET_NAME
    AWS_S3_REGION_NAME = AWS_S3_REGION_NAME
    AWS_LOCATION = AWS_LOCATION

    # recommended django-storages settings
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None

    MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{AWS_LOCATION}/" # noqa
else:
    # fall back to local media for development
    MEDIA_URL = "/media/"

# FTP Server Configuration
FTPSERVER_DIRECTORY = MEDIA_ROOT
FTPSERVER_FILESYSTEM = "CONFIG.filesystems.StorageFS"
FTPSERVER_PORT = 2121

# Optional: configure a public IP or hostname that the FTP server advertises
# for PASV (passive) connections. Set this to your Lightsail public IP or
# public domain if the instance is behind NAT. Example:
FTPSERVER_MASQUERADE_ADDRESS = FTPSERVER_MASQUERADE_ADDRESS  # replace with your public IP

# Optional: configure a passive port range (server uses these ports for
# data connections in PASV mode). Make sure to open this range in Lightsail
# and OS firewall. Example:
FTPSERVER_PASSIVE_PORTS = FTPSERVER_PASSIVE_PORTS

# Optional: To accept PORT/active connections to foreign IPs (not recommended
# for most deployments) you can set a custom handler where
# `permit_foreign_addresses = True`. See CONFIG/ftp_handler.py for an example.
FTPSERVER_HANDLER = 'CONFIG.ftp_handler.PermissiveFTPHandler'
