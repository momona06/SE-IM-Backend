import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = '/static/'  # 通过别名指向STATICFILES_DIRS目录，当然，别名也可以修改
STATIC_ROOT = os.path.join(BASE_DIR, 'collect_static')
STATICFILES_DIRS = [  # 列表或者元组都行
    os.path.join(BASE_DIR, 'static')  # 你也可以配置多个静态文件目录，只需拼上路径就好了
]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(STATIC_ROOT, 'media')

SECRET_KEY = 'django-insecure-xvv16d@^4vu6-_^8w73_wt+xqf-wfppqevn)_zgye!#7l^6=p$'

envDep = os.getenv('DEPLOY')
if envDep is None:
    DEBUG = True
else:
    DEBUG = False

ALLOWED_HOSTS = [
    '*'
]


# Application definition

INSTALLED_APPS = [
    'channels',
    'channels_postgres',
    'daphne',
    'FriendRelation',
    'UserManage',
    'Chat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'IM_Backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

ASGI_APPLICATION = "IM_Backend.asgi.application"

# 部署CHANNEL_LAYER
if not DEBUG:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_postgres.core.PostgresChannelLayer',
            'CONFIG': {
                'HOST': 'database-postgresql.OverFlowLab.secoder.local',
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'postgres',
                'PORT': 5432,
                'USER': 'postgres',
                'PASSWORD': '123456'
            },
        },
    }

# 本地CHANNEL_LAYER
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_postgres.core.PostgresChannelLayer',
            'CONFIG': {
                'HOST': '127.0.0.1',
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'postgres',
                'PORT': 5432,
                'USER': 'postgres',
                'PASSWORD': '1234'
            },
        },
    }


# 部署PostGreSQL
if not DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'postgres',                                       # 连接的数据库
            'HOST': 'database-postgresql.OverFlowLab.secoder.local',  # ip地址
            'PORT': 5432,                                             # 端口
            'USER': 'postgres',                                       # 用户名
            'PASSWORD': '123456'                                      # 密码
        },
        'channels_postgres': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'postgres',                                       # 连接的数据库
            'HOST': 'database-postgresql.OverFlowLab.secoder.local',  # ip地址
            'PORT': 5432,                                             # 端口
            'USER': 'postgres',                                       # 用户名
            'PASSWORD': '123456'                                      # 密码
        }
    }


# 本地PostGreSQL
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'postgres',   # 连接的数据库
            'HOST': '127.0.0.1',  # 网址
            'PORT': 5432,         # 端口
            'USER': 'postgres',   # 用户名
            'PASSWORD': '1234'    # 密码
        },
        'channels_postgres': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'postgres',   # 连接的数据库
            'HOST': '127.0.0.1',  # 网址
            'PORT': 5432,         # 端口
            'USER': 'postgres',   # 用户名
            'PASSWORD': '1234'    # 密码
        }
    }

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = "smtp.qq.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "2840206224@qq.com"
EMAIL_HOST_PASSWORD = "yeqobqvmlxlpdghg"
EMAIL_USE_TLS = False
EMAIL_FROM = "2840206224@qq.com"

AUTH_PASSWORD_VALIDATORS = [{
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    }, {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    }, {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    }, {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
