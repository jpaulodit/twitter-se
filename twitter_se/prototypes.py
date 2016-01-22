import sys
import os
import hashlib

# definition of the django settings

from django.conf import settings

# tries to get value of debug from environment variables and set to on as default
DEBUG = os.environ.get('DEBUG', 'on') == 'on'

# get secret key from env variables else set to some random string of 32 len.
SECRET_KEY = os.environ.get('SECRET_KEY', '{{ secret_key }}')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

BASE_DIR = os.path.dirname(__file__)

CONSUMER_KEY = os.environ.get('CONSUMER_KEY', '123')
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET', 'abc')

settings.configure(
	ALLOWED_HOSTS=ALLOWED_HOSTS,
	DEBUG=DEBUG,
	SECRET_KEY=SECRET_KEY,
	ROOT_URLCONF='twittersearch.urls',
    INSTALLED_APPS=(
        'django.contrib.staticfiles',
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'twittersearch',
    ),
    TEMPLATES=(
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
        },
    ),

	MIDDLEWARE_CLASSES=(
			'django.contrib.sessions.middleware.SessionMiddleware',
			'django.contrib.auth.middleware.AuthenticationMiddleware',
			'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
		),

    CACHES = {
		'default' : {
			'BACKEND' : 'django.core.cache.backends.memcached.PyLibMCCache',
			'LOCATION': '127.0.0.1:11211',
			'TIMEOUT' : None,
		}
	},

	SESSION_ENGINE=('django.contrib.sessions.backends.cache'),

    CONSUMER_KEY=CONSUMER_KEY,
    CONSUMER_SECRET=CONSUMER_SECRET,

	STATICFILES_DIRS=(os.path.join(BASE_DIR, 'twittersearch/static'),),
	STATIC_URL='/static/',
	SITE_PAGES_DIRECTORY=os.path.join(BASE_DIR, 'pages'),
)


### For use after development.
# from django.core.wsgi import get_wsgi_application
# application = get_wsgi_application()


if __name__ == "__main__":
	from django.core.management import execute_from_command_line
	execute_from_command_line(sys.argv)