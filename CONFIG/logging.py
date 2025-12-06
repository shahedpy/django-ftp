# PYTHON IMPORTS
import os

# SETTINGS IMPORTS
from .local_settings import LOGS_DIR


# if not exists, create
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {module} {process:d} {thread:d} '
                      '{message}',
            'style': '{',
        },
        'simple': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
    },  # formatters
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'verbose',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, "debug.log"),
            'when': 'midnight',
            'backupCount': 30,
        },
    },  # handlers
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO').upper(),
        },
        'Core': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG').upper(),
            'propagate': False,  # required to eliminate duplication on root
        },
        'API': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG').upper(),
            'propagate': False,  # required to eliminate duplication on root
        },
        # 'app_name': {
        #     'handlers': ['console', 'file'],
        #     'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG').upper(),
        #     'propagate': False,  # required to eliminate duplication on root
        # },
    },  # loggers
}  # logging