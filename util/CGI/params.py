# -*- coding: utf-8 -*-

from __future__ import absolute_import

import operator
import itertools
import re
import cgi
import urllib
import urlparse
from StringIO import StringIO

import config

from util.CGI.headers import _DictHeaders, Headers

def _safe_headers(req):
	headers_list = ('Content-Type', 'Content-Length', 'Content-Disposition')
	rc = _DictHeaders(Headers())
	for headers_item in headers_list:
		try:
			rc[headers_item] = req.request_headers[headers_item]
		except KeyError:
			pass
	return rc

def _params_ex(fs, param, not_found_exc):
	if fs is None:
		raise not_found_exc()

	if param in fs:
		objs = fs[param]
		if not (type(objs) is type([])):
			 objs = [objs]
	else:
		objs = []

	return objs

class Params(object):
	class NotFoundError(Exception):
		pass

	class ParseError(Exception):
		pass

	def __init__(self, req, parse_query_string=False, parse_request_body=False):
		if parse_query_string and req.query_string:
			try:
				self._fs_GET = urlparse.parse_qs(req.query_string, True, True)
			except ValueError:
				raise self.ParseError()
		else:
			self._fs_GET = None

		if parse_request_body and req.request_body:
			try:
				self._fs_POST = cgi.FieldStorage(StringIO(req.request_body), _safe_headers(req), environ={'REQUEST_METHOD': 'POST'}, keep_blank_values=True, strict_parsing=True)
			except ValueError, err:
				raise self.ParseError()
		else:
			self._fs_POST = None

	def param_get(self, param):
		value_iterator = iter(self.paramlist_get(param))
		try:
			return value_iterator.next()
		except StopIteration:
			raise self.NotFoundError

	def paramlist_get(self, param):
		return _params_ex(self._fs_GET, param, self.NotFoundError)

	def _paramlist_post(self, param):
		return (
			itertools.imap(lambda item_map: str(item_map.value),
				itertools.ifilter(lambda item_filter: item_filter.filename is None,
					_params_ex(self._fs_POST, param, self.NotFoundError)
				)
			)
		)

	def param_post(self, param):
		value_iterator = self._paramlist_post(param)
		try:
			return value_iterator.next()
		except StopIteration:
			raise self.NotFoundError

	def paramlist_post(self, param):
		return list(self._paramlist_post(param))

	def file(self, param):
		value_iterator = self._filelist(param)
		try:
			return value_iterator.next()
		except StopIteration:
			raise self.NotFoundError

	def _filelist(self, param):
		return (
			itertools.imap(lambda item_map: item_map,
				itertools.ifilter(lambda item_filter: item_filter.filename is not None,
					_params_ex(self._fs_POST, param, self.NotFoundError)
				)
			)
		)

	def filelist(self, param):
		return list(self._filelist(param))

