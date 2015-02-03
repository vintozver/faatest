# -*- coding: utf-8 -*-

from __future__ import absolute_import

import redis

import util.context
import config


class DbSessionController(util.context.AutoRefContextItem):
	def new(self):
		db_session = redis.Redis(host=config.main.db_cache['host'], port=config.main.db_cache['port'], db=config.main.db_cache['index'], password=config.main.db_cache['password'])
		self._value = db_session
	def delete(self):
		try:
			db_session = self._value
		except AttributeError:
			return
		db_session.connection_pool.disconnect()
		try:
			del self._value
		except AttributeError:
			pass
	def value(self):
		return self._value


def session_wrapper_context(param='db_session_cache'):
	'''Wraps function for accepting db_session parameter
If db_session parameter is None or omitted, new database session is created and controlled'''
	def _wrapper(function):
		def controller(*args, **kwargs):
			ctx = util.context.GreenletContext()
			ctx.ref(param, DbSessionController)
			try:
				return function(*args, **kwargs)
			finally:
				ctx.unref(param)
		return controller
	return _wrapper
def session_access_context(param='db_session_cache'):
	return util.context.GreenletContext()[param]

