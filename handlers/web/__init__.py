# -*- coding: utf-8 -*-

from __future__ import absolute_import

import functools
import sys
import os
import datetime
import dateutil.relativedelta
import pytz
import re
import urllib
import urlparse
import httplib

import config

import modules.templates.filesystem as mod_tmpl_fs
import modules.data.mongo as mod_mongo

from modules.wrappers.session import MongoDbSession as _SessionBase
class GroundSchoolSession(_SessionBase):
	db_name = config.main.db_mongo['name']
	db_collection = 'sessions'

class SessionControlCaller(object):
	def __init__(self, function, attr, instance, owner):
		self.function = function
		self.attr = attr
		self.instance = instance
		self.owner = owner
	def __call__(self, *args, **kwargs):
		if self.instance == None:
			raise AssertionError('Object is required')
		try:
			req = self.instance.req
		except AttributeError:
			raise AssertionError('Object with req attribute is required')
		@mod_mongo.session_wrapper_context()
		def _wrapper(*args, **kwargs):
			db_session = mod_mongo.session_access_context()
			expiration = pytz.timezone(config.main.timezone).normalize(pytz.timezone('UTC').localize(datetime.datetime.utcnow())) + dateutil.relativedelta.relativedelta(hours=4)
			setattr(req, self.attr, GroundSchoolSession(req, 'ground_school_secret_###', db_session, cookie='ground_school_session_id', expiration=expiration))
			try:
				method = self.function.__get__(self.instance, self.owner)
				return method(*args, **kwargs)
			finally:
				delattr(req, self.attr)
		_wrapper()

class SessionControlWrapper(object):
	def __init__(self, function, attr):
		self.function = function
		self.attr = attr
	def __get__(self, instance, owner):
		method = self.function.__get__(instance, owner)
		return functools.update_wrapper(SessionControlCaller(self.function, self.attr, instance, owner), method, functools.WRAPPER_ASSIGNMENTS, {})

class SessionControl(object):
	def __init__(self, attr='Session'):
		super(SessionControl, self).__init__()
		self.attr = attr

	def __call__(self, function):
		return SessionControlWrapper(function, self.attr)


from util.handler import HandlerError as _base_error
class HandlerError(_base_error):
	pass

class SubHandlerError(HandlerError):
	pass

class NotFoundError(HandlerError):
	pass

from util.handler import Handler as _base
class Handler(_base):
	def _handle_root(self):
		path = urllib.unquote(urlparse.urlparse(self.req.uri).path)

		module_name = None

		match = re.match(r'^/test/(\d+)$', path)
		if match != None:
			return 'handlers.web.tests', {'id': match.group(1)}
		match = re.match(r'^/(\w+)\.(py|php)$', path)
		if match != None:
			return 'handlers.web.%s' % match.group(1), {}
		match = re.match(r'^/$', path)
		if match != None:
			return 'handlers.web.index', {}

		raise NotFoundError('Обработчик не найден')

	@SessionControl('GroundSchoolSession')
	def __call__(self):
		try:
			try:
				module_name, module_params = self._handle_root()
				__import__(module_name)
				return sys.modules[module_name].Handler(self.req)(**module_params)
			except NotFoundError:
				path = urllib.unquote(urlparse.urlparse(self.req.uri).path)
				rel_path = path
				if rel_path.find('/') != 0:
					raise HandlerError('Попытка взлома! Допускается только полный путь к документу')
				rel_path = rel_path[1:]
				static_base = os.path.normpath(os.path.join(config.main.basedir, 'htdocs'))
				static_path = os.path.normpath(os.path.join(static_base, rel_path))
				if os.path.commonprefix((static_base, static_path)) != static_base:
					raise HandlerError('Попытка взлома! Путь не находится в базовом каталоге статических файлов')
				if os.path.isfile(static_path):
					import handlers.ext.static as _mod
					return _mod.Handler(self.req)(path=static_path)
				else:
					raise NotFoundError('Запрашиваемый документ не найден')
		except NotFoundError, err:
			try:
				content = mod_tmpl_fs.TemplateFactory('error_notfound').render({'description': err.args[0]})
			except mod_tmpl_fs.TemplateError:
				raise HandlerError('Template error')
			self.req.setResponseCode(httplib.NOT_FOUND, httplib.responses[httplib.NOT_FOUND])
			self.req.setHeader('Content-Type', 'text/html; charset=utf-8')
			self.req.write(content)
		except:
			import traceback
			err_type, err_value, err_tb = sys.exc_info()
			tb = reduce(
				lambda line_up, line_down: line_up + '\n' + line_down,
				map(
					lambda item: '%s: %s' % (item[0], item[1]),
					traceback.extract_tb(err_tb)
				)
			)
			try:
				content = mod_tmpl_fs.TemplateFactory('error_internal').render({
				'return_url': '',
				'description': '''\
При обработке запроса произошла ошибка\n
Тип ошибки: %s\n
Значение ошибки: %s\n
Информация для разработчика:\n%s\
''' % (err_value.__class__.__name__, str(err_value), tb),
				})
			except mod_tmpl_fs.TemplateError:
				raise err_type, err_value, err_tb
			self.req.setResponseCode(httplib.INTERNAL_SERVER_ERROR, httplib.responses[httplib.INTERNAL_SERVER_ERROR])
			self.req.setHeader('Content-Type', 'text/html; charset=utf-8')
			self.req.write(content)
			raise err_type, err_value, err_tb

