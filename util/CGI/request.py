# -*- coding: utf-8 -*-

from __future__ import absolute_import

import types
import operator
import urlparse
import datetime

from util.CGI.headers import Headers, _DictHeaders


class RequestException(BaseException):
	pass

class Request(object):
	def __new__(cls, env, responder):
		self = object.__new__(cls)

		from util.context import Context
		self.context = Context()
		self.env = env

		_self_env_get = self.env.get # Optimize frequent method access

		self.method = _self_env_get('REQUEST_METHOD', 'GET')
		self.path = _self_env_get('PATH_INFO', '/')
		self.query_string = _self_env_get('QUERY_STRING', '')
		self.uri = urlparse.urlunsplit(('', '', self.path, self.query_string, ''))
		self.clientproto = _self_env_get('SERVER_PROTOCOL', 'HTTP/0.9')

		self.client_address = _self_env_get('REMOTE_ADDR', '')
		self.client_host = _self_env_get('REMOTE_HOST', '')
		self.remote_user = _self_env_get('REMOTE_USER', None)
		self.remote_ident = _self_env_get('REMOTE_IDENT', None)

		self.requestHeaders = Headers()
		self.responseHeaders = Headers()
		self.received_cookies = {}
		self.cookies = [] # outgoing cookies

		self.request_body = self.env['wsgi.input'].read()
		self.response_body = []

		self._parseHeaders()
		self._parseCookies()

		self.status_code = 200
		self.status_message = 'OK'

		self.setHeader('Date', datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'))

		self.response_iterator = self()
		self.response_writer = responder('%d %s' % (self.status_code, self.status_message), reduce(operator.add, map(lambda (header_name, header_values): zip((header_name, ) * len(header_values), header_values), self.responseHeaders.getAllRawHeaders()), []))
		# do not use writer unless you know what you exactly do!
		try:
			body_chunks = len(self.response_body)
			if self.response_iterator != None:
				body_chunks = body_chunks + len(self.response_iterator)
		except TypeError:
			body_chunks = None
		if body_chunks != None:
			def len_method(self):
				return body_chunks
			self.__len__ = types.MethodType(len_method, self, self.__class__)

		return self

	def __repr__(self):
		return '<%s %s %s>'% (self.method, self.uri, self.clientproto)

	def __iter__(self):
		for data in self.response_body:
			yield data
		if self.response_iterator != None:
			for data in self.response_iterator:
				if isinstance(data, unicode):
					data = data.encode('utf-8')
				if isinstance(data, str):
					yield data
				else:
					raise TypeError('data type must be "str" or "unicode"')

	def _parseHeaders(self):
		def env2name(env):
			return env.split('HTTP_', 1)[1].replace('_', '-').lower()
		for header_name, header_value in map(lambda (header_name, header_value): (env2name(header_name), header_value), filter(lambda (header_name, header_value): header_name.startswith('HTTP_'), self.env.items())):
			self.requestHeaders.setRawHeaders(header_name, [header_value])
		if 'CONTENT_LENGTH' in self.env:
			self.requestHeaders.setRawHeaders('Content-Length', [self.env['CONTENT_LENGTH']])
		if 'CONTENT_TYPE' in self.env:
			self.requestHeaders.setRawHeaders('Content-Type', [self.env['CONTENT_TYPE']])

	def _parseCookies(self):
		"""
		Parse cookie headers.

		This method is not intended for users.
		"""
		cookieheaders = self.requestHeaders.getRawHeaders("cookie")

		if cookieheaders is None:
			return

		for cookietxt in cookieheaders:
			if cookietxt:
				for cook in cookietxt.split(';'):
					cook = cook.lstrip()
					try:
						k, v = cook.split('=', 1)
						self.received_cookies[k] = v
					except ValueError:
						pass

	def __setattr__(self, name, value):
		"""
		Support assignment of C{dict} instances to C{request_headers} for
		backwards-compatibility.
		"""
		if name == 'request_headers':
			# A property would be nice, but Request is classic.
			self.requestHeaders = headers = Headers()
			for k, v in value.iteritems():
				 headers.setRawHeaders(k, [v])
		elif name == 'requestHeaders':
			self.__dict__[name] = value
			self.__dict__['request_headers'] = _DictHeaders(value)
		elif name == 'response_headers':
			self.responseHeaders = headers = Headers()
			for k, v in value.iteritems():
				 headers.setRawHeaders(k, [v])
		elif name == 'responseHeaders':
			self.__dict__[name] = value
			self.__dict__['response_headers'] = _DictHeaders(value)
		else:
			self.__dict__[name] = value

	def isSecure(self):
		return 'HTTPS' in self.env

	def setResponseCode(self, code, message):
		"""
		Set the HTTP response code and message.
		"""
		if not isinstance(code, (int, long)):
			raise TypeError("HTTP response code must be int or long")
		if not isinstance(message, (str)):
			raise TypeError("HTTP response message must be str")
		self.status_code = code
		self.status_message = message

	# The following is the public interface that people should be
	# writing to.
	def getHeader(self, key):
		"""
		Get an HTTP request header.

		@type key: C{str}
		@param key: The name of the header to get the value of.

		@rtype: C{str} or C{NoneType}
		@return: The value of the specified header, or C{None} if that header
			was not present in the request.
		"""
		value = self.requestHeaders.getRawHeaders(key)
		if value is not None:
			return value[-1]

	def setHeader(self, name, value):
		"""
		Set an HTTP response header.  Overrides any previously set values for
		this header.

		@type name: C{str}
		@param name: The name of the header for which to set the value.

		@type value: C{str}
		@param value: The value to set for the named header.
		"""
		self.responseHeaders.setRawHeaders(name, [value])

	def getCookie(self, key):
		"""
		Get a cookie that was sent from the network.
		"""
		return self.received_cookies.get(key)

	def addCookie(self, k, v, expires=None, domain=None, path=None, max_age=None, comment=None, secure=None):
		"""
		Set an outgoing HTTP cookie.
		"""
		cookie = '%s=%s' % (k, v)
		if expires is not None:
			cookie = cookie +"; Expires=%s" % expires
		if domain is not None:
			cookie = cookie +"; Domain=%s" % domain
		if path is not None:
			cookie = cookie +"; Path=%s" % path
		if max_age is not None:
			cookie = cookie +"; Max-Age=%s" % max_age
		if comment is not None:
			cookie = cookie +"; Comment=%s" % comment
		if secure:
			cookie = cookie +"; Secure"
		self.cookies.append(cookie)

	def write(self, data):
		if not self.response_body:
			for cookie in self.cookies:
				self.responseHeaders.addRawHeader('Set-Cookie', str(cookie))
		if isinstance(data, unicode):
			data = data.encode('utf-8')
		if isinstance(data, str):
			self.response_body.append(data)
		else:
			raise TypeError('data type must be "str" or "unicode"')

