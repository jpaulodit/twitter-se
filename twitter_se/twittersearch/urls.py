
from django.conf.urls import url

from .views import page
from .views import search_tweet
from .views import oauth_login
from .views import oauth_callback
from .views import logout

urlpatterns = (
	url(r'^callback$', oauth_callback, name='oauth_callback'),
	url(r'^login/$', oauth_login, name='oauth_login'),
	url(r'^logout/$', logout, name='logout'),
	url(r'^index/search_tweet/$', search_tweet, name='search_tweet'),
	url(r'^search_tweet/$', search_tweet, name='search_tweet'),
	url(r'^(?P<slug>[\w./-]+)/$', page, name='page'),
	url(r'^$', page, name='homepage'),		
)

