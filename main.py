from bs4 import BeautifulSoup, NavigableString
from urllib.request import urlopen, Request
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from proxy_requests import ProxyRequests


def fetch(url, headers):
	try:
		html_response = urlopen(Request(url, headers=headers))
		return html_response.read()
	except:
		return fetch_with_proxy(url, headers)

def fetch_with_proxy(url, headers):
	r = ProxyRequests(url)
	if headers:
		r.set_headers(headers)
		r.get_with_headers()
	else:
		r.get()

	status_code = r.get_status_code()
	if status_code != 200:
		print(f"{status_code}: {url}")

	return r.get_raw()

@dataclass
class Tweet:
	username: str
	full_name: str
	text: str
	date_posted: datetime

	@staticmethod
	def hydrate(tweet_id: str) -> Optional['Tweet']:
		soup = Tweet._get_soup(tweet_id)

		if not soup:
			return
		
		return Tweet(
			username=Tweet._get_tweet_username(soup),
			full_name=Tweet._get_tweet_full_name(soup),
			text=Tweet._get_tweet_text(soup),
			date_posted=Tweet._get_tweet_date_posted(soup),
		)

	@staticmethod
	def _get_soup(tweet_id: str) -> Optional[BeautifulSoup]:
		url = f"https://twitter.com/anyuser/status/{tweet_id}"
		agent = "Mozilla/5.0 (compatible;  MSIE 7.01; Windows NT 5.0)"
		html_response = fetch(url, headers={'User-Agent': agent})
		
		if not html_response:
			return None

		html_source = html_response.decode('utf-8')
		soup = BeautifulSoup(html_source, features="lxml")
		tweet_text_div = soup.find("div", {"class": "tweet-text"})

		# Twitter account is probably suspended or tweet deleted
		if not tweet_text_div:
			return None
		
		return soup

	@staticmethod
	def _get_tweet_text(soup: BeautifulSoup) -> Optional[str]:
		tweet_text_div = soup.find("div", {"class": "tweet-text"})

		tweet_components = []
		for child in tweet_text_div.children:
			if isinstance(child, NavigableString):
				continue

			tweet_components.append(child.text)

		return " ".join(tweet_components).strip()
	
	@staticmethod
	def _get_tweet_username(soup: BeautifulSoup) -> str:
		username_span = soup.find("span", {"class": "username"})
		return username_span.text

	@staticmethod
	def _get_tweet_full_name(soup: BeautifulSoup) -> str:
		full_name_div = soup.find("div", {"class": "fullname"})
		full_name_strong_tag = full_name_div.find("strong")
		return full_name_strong_tag.text

	@staticmethod
	def _get_tweet_date_posted(soup: BeautifulSoup) -> datetime:
		metadata_div = soup.find("div", {"class": "metadata"})
		datetime_string = metadata_div.find("a").text
		date_posted = datetime.strptime(datetime_string, "%H:%M %p - %d %b %Y")
		return date_posted