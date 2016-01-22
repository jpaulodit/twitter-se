import os
import base64
import json
import sys

from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.template import Template
from django.utils._os import safe_join
from django.utils.http import urlencode

from django.core.cache import cache

from urllib.request import urlopen, Request
from urllib.error import HTTPError

from twython import Twython

from django.contrib.auth import authenticate, login, logout as django_logout
from django.contrib.auth import get_user_model


TWITTER_END_PT = 'https://api.twitter.com/'
TWITTER_API_VER = '1.1'
REQUEST_TOKEN_URL = TWITTER_END_PT + 'oauth2/token'
SEARCH_TWEET_URL = TWITTER_END_PT + TWITTER_API_VER + '/search/tweets.json'



def get_data_using_oauth2(q):

	"""Application-only Authentication"""

	if settings.DEBUG:
		print('Getting data using OAUTH2')

	consumer_key = settings.CONSUMER_KEY
	consumer_secret = settings.CONSUMER_SECRET
	twitter = Twython(consumer_key, consumer_secret, oauth_version=2)
	ACCESS_TOKEN = twitter.obtain_access_token()
	twitter = Twython(consumer_key, access_token=ACCESS_TOKEN)
	data = twitter.search(q=q)
	return data



def get_data_using_oauth1(request, q):

	"""Implementing sign in with Twitter"""

	if settings.DEBUG:
		print('Getting data using OAUTH1')

	consumer_key = settings.CONSUMER_KEY
	consumer_secret = settings.CONSUMER_SECRET
	oauth_token = request.session.get('oauth_token')
	oauth_token_secret = request.session.get('oauth_token_secret')
	twitter = Twython(consumer_key, consumer_secret, oauth_token, oauth_token_secret)
	data = twitter.search(q=q)
	return data



def process_tweets(data):

	"""Process tweet data and extract required information"""

	hashtag_tracker = {}
	tweet_list = []

	num_tweets = data['search_metadata']['count']
	if num_tweets > 0:

		for tweet in data['statuses']:

			content = tweet['text']
			name = tweet['user']['name']
			num_fav = tweet['favorite_count']

			tweet_info = {}
			tweet_info['name'] = name
			tweet_info['text'] = content
			tweet_info['num_fav'] = num_fav

			tweet_list.append(tweet_info)

			# count number of hashtags in the tweet and track
			hashtags = tweet['entities']['hashtags']
			for hashtag in hashtags:
				hashtag_text = hashtag['text']
				if hashtag_text in hashtag_tracker:
					hashtag_tracker[hashtag_text] += 1
				else:
					hashtag_tracker[hashtag_text] = 1


	# need to put into list because the hashtag might be like "items" which
	# is a method, and that would affect our loop in the template.
	hashtag_list = []
	for hashtag, cnt in hashtag_tracker.items():
		hashtag_list.append({'name' : hashtag, 'count' : cnt})

	context = {
		'hashtag_tbl' : hashtag_list,
		'tweet_tbl' : tweet_list,
	}

	return context



def search_tweet(request):

	"""pass user query to Twitter API and return result"""

	tweet_q = request.GET.get('query', '')

	if tweet_q:
		
		encoded_tweet_q = urlencode({'q': tweet_q})

		data = cache.get(encoded_tweet_q)

		if data is None:
			
			if request.session.get('username') and request.session.get('oauth_token') and request.session.get('oauth_token_secret'):
				# get data using user's token
				data = get_data_using_oauth1(request, tweet_q)

			else:
				# get data using application's token
				data = get_data_using_oauth2(tweet_q)

			if 'error' in data:
				# error: user query too complex
				return HttpResponseBadRequest('Bad Request<br><a href="/">Home</a>')
			else:
				# set data to expire after 30 seconds
				cache.set(encoded_tweet_q, data, 30)
		

		context = process_tweets(data)

		context['slug'] = 'result'

		page = get_page_or_404('result.html')
		context['page'] = page
		context['person'] = request.session.get('username', None)

		return render(request, 'page.html', context)
	

	else:		
		# error: query is somehow empty
		return HttpResponseServerError('Internal Server Error<br><a href="/">Home</a>')



def logout(request):

	"""Clear user session"""

	request.session.flush()
	return redirect('/')

	
def oauth_callback(request):

	"""Callback after user enters his/her twitter client_credentials"""

	oauth_token = request.GET.get('oauth_token')
	oauth_verifier = request.GET.get('oauth_verifier')

	orig_oauth_token = request.session.get('oauth_token')
	orig_oauth_token_secret = request.session.get('oauth_token_secret')

	# need to verify the oauth token matches.
	if oauth_token == orig_oauth_token:
		twitter = Twython(settings.CONSUMER_KEY, settings.CONSUMER_SECRET, 
							orig_oauth_token, orig_oauth_token_secret)


		authorized_tokens = twitter.get_authorized_tokens(oauth_verifier)

		request.session['username'] = authorized_tokens['screen_name']
		request.session['oauth_token'] = authorized_tokens['oauth_token']
		request.session['oauth_token_secret'] = authorized_tokens['oauth_token_secret']


	return redirect('/')


def oauth_login(request):

	"""OAUTH Login for user to login via Twitter""" 

	twitter = Twython(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)

	auth = twitter.get_authentication_tokens(callback_url='http://127.0.0.1:8000/callback')

	if auth['oauth_callback_confirmed'] == 'true':

		OAUTH_TOKEN = auth['oauth_token']
		OAUTH_TOKEN_SECRET = auth['oauth_token_secret']

		request.session['oauth_token'] = OAUTH_TOKEN
		request.session['oauth_token_secret'] = OAUTH_TOKEN_SECRET
		request.session['next_url'] = request.GET.get('next', None)

		auth_url = auth['auth_url']
		return redirect(auth_url)

	else:

		return redirect('/')



def page(request, slug='index'):

	"""Render the requested page if found."""

	file_name = '{}.html'.format(slug)
	page = get_page_or_404(file_name)
	context = {
		'slug' : slug,
		'page' : page,
		'person' : request.session.get('username', None)
	}

	return render(request, 'page.html', context)	



def get_page_or_404(name):

	"""Return page content as a Django template or raise 404 error."""

	try:
		file_path = safe_join(settings.SITE_PAGES_DIRECTORY, name)
	except ValueError:
		raise Http404('Page Not Found')
	else:
		print(file_path)
		if not os.path.exists(file_path):
			raise Http404('Page Not Found')

	with open(file_path, 'r') as file_handler:
		page = Template(file_handler.read())

	return page
