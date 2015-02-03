import cgi
import urllib
import urlparse
import xml.sax.saxutils
import datetime
import time
import calendar

def map_not_None(value, function):
	if value != None:
		return function(value)
	else:
		return None

def html_input_escape(value):
	return cgi.escape(value, True)

def html_attribute(value):
	if type(value) == unicode:
		value = value.encode('utf-8')
	if type(value) != str:
		value = str(value)
	return xml.sax.saxutils.quoteattr(value)

import HTMLParser
class MLStripper(HTMLParser.HTMLParser):
	def __init__(self):
		self.reset()
		self.fed = []
	def handle_data(self, d):
		self.fed.append(d)
	def get_data(self):
		return ''.join(self.fed)
def html_strip(value):
	processor = MLStripper()
	processor.feed(value)
	return processor.get_data()

def select_not_None(*args):
	for arg in args:
		if arg != None:
			return arg
	return None

def build_url(scheme=None, netloc='', path='', query='', fragment=''):
	if not scheme and netloc:
		scheme = 'http'
	try:
		query_str = urllib.urlencode(query)
	except TypeError:
		query_str = urllib.quote(query)
	return urlparse.urlunsplit(urlparse.SplitResult(scheme=scheme, netloc=netloc, path=path, query=query_str, fragment=fragment))

def resize_image_png(stream, width, height):
	"""
	Resize image to fit it into (width, height) box.
	Returns stream
	"""
	try:
		import Image
	except ImportError:
		from PIL import Image
	image = Image.open(stream)
	oldw, oldh = image.size
	if oldw >= oldh:
		x = int(round((oldw - oldh) / 2.0))
		image = image.crop((x, 0, (x + oldh) - 1, oldh - 1))
	else:
		y = int(round((oldh - oldw) / 2.0))
		image = image.crop((0, y, oldw - 1, (y + oldw) - 1))
	image = image.resize((width, height), resample=Image.ANTIALIAS)

	from StringIO import StringIO
	string = StringIO()
	image.save(string, format='PNG')
	string.seek(0)
	return string

def resize_image_jpg(stream, width, height):
	"""
	Resize image to fit it into (width, height) box.
	Returns stream
	"""
	try:
		import Image
	except ImportError:
		from PIL import Image
	image = Image.open(stream)
	oldw, oldh = image.size
	if oldw >= oldh:
		x = int(round((oldw - oldh) / 2.0))
		image = image.crop((x, 0, (x + oldh) - 1, oldh - 1))
	else:
		y = int(round((oldh - oldw) / 2.0))
		image = image.crop((0, y, oldw - 1, (y + oldw) - 1))
	image = image.resize((width, height), resample=Image.ANTIALIAS)

	from StringIO import StringIO
	string = StringIO()
	image.save(string, format='JPEG')
	string.seek(0)
	return string

def datetime_utc_to_local(val, tz=None):
	return datetime.datetime.fromtimestamp(calendar.timegm(val.utctimetuple()), tz)

