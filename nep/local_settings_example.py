import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'w&hkq685h_b37nsph31m@t$^5bf3^q98+2!chqno+#@89y%ah9'

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1']

DEV_APPS = []

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

TIME_ZONE = 'America/Sao_Paulo'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
