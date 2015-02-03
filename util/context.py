# -*- coding: utf-8 -*-

from __future__ import absolute_import

import types
import operator


class Context(object):
	def __init__(self):
		self.items = {}

	def ref(self, param, item_creator):
		try:
			obj = self.items[param]
		except KeyError:
			obj = item_creator()
			self.items[param] = obj
		obj.ref()
		if not obj.isref():
			del self.items[param]
	def unref(self, param):
		try:
			obj = self.items[param]
		except KeyError:
			raise ContextError('Param is unknown', param)
		obj.unref()
		if not obj.isref():
			del self.items[param]

	def __getattr__(self, attr):
		return self[attr]

	def __getitem__(self, param):
		try:
			obj = self.items[param]
		except KeyError:
			raise ContextError('Param is unknown', param)
		return obj.value()
	def __setitem__(self, param, value):
		raise NotImplementedError('Use ref/unref methods to control the value')
	def __delitem__(self, param):
		raise NotImplementedError('Manual item deletion is forbidden. Use ref/unref methods')

class ContextItem(object):
	def ref(self):
		raise NotImplementedError
	def unref(self):
		raise NotImplementedError
	def isref(self):
		raise NotImplementedError
	def value(self):
		raise NotImplementedError

class AutoRefContextItem(ContextItem):
	def __init__(self):
		self.counter = 0
	def ref(self):
		if not self.counter:
			self.new()
		self.counter = self.counter + 1
	def unref(self):
		self.counter = self.counter - 1
		if not self.counter:
			self.delete()
	def isref(self):
		return bool(self.counter)

	def new(self):
		raise NotImplementedError
	def delete(self):
		raise NotImplementedError

class ContextError(Exception):
	pass

class FakeRequest(object):
	def __init__(self):
		self.context = Context()

try:
	import greenlet
except ImportError:
	pass
else:
	class GreenletContext(Context):
		def __init__(self):
			_greenlet = greenlet.getcurrent()
			try:
				ctx = _greenlet.ctx
			except AttributeError:
				ctx = dict()
				_greenlet.ctx = ctx
			self.items = ctx

