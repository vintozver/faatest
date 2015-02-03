# -*- coding: utf-8 -*-

from __future__ import absolute_import
import types

import bson.son
import pymongo


import util.context
import config


class DbSessionController(util.context.AutoRefContextItem):
	def new(self):
		db_session = pymongo.MongoClient(config.main.db_mongo['host'], config.main.db_mongo['port'])
		if config.main.db_mongo['user']:
			db_session[config.main.db_mongo['name']].authenticate(config.main.db_mongo['user'], config.main.db_mongo['password'])
		self._value = db_session
	def delete(self):
		try:
			db_session = self._value
		except AttributeError:
			return
		try:
			del self._value
		except AttributeError:
			pass
	def value(self):
		return self._value

def session_wrapper_context(param='db_session_mongo'):
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
def session_access_context(param='db_session_mongo'):
	return util.context.GreenletContext()[param]


from UserDict import DictMixin
class DataObject(object, DictMixin):
	class _Error(Exception):
		pass

	@classmethod
	def schema_init(cls):
		pass

	def __init__(self):
		self.data = dict()

	def __getitem__(self, key):
		return self.data.__getitem__(key)

	def __setitem__(self, key, value):
		return self.data.__setitem__(key, value)

	def __delitem__(self, key):
		return self.data.__delitem__(key)

	def __contains__(self, key):
		return self.data.__contains__(key)

	def __iter__(self):
		return self.data.__iter__()

	def __len__(self):
		return self.data.__len__()

	@classmethod
	def create_from_data(cls, data):
		obj = cls()
		obj.data = data
		return obj


class CounterObject(DataObject):
	@classmethod
	@session_wrapper_context()
	def _collection(cls):
		db_session = session_access_context()
		thecollection = db_session[config.main.db_mongo['name']]['counters']
		return thecollection

	@classmethod
	@session_wrapper_context()
	def schema_init(cls):
		db_session = session_access_context()
		thecollection = cls._collection()
		thecollection.ensure_index('collection', unique=True)

	@session_wrapper_context()
	def counter_init(self, collection_name, initial=1):
		db_session = session_access_context()
		thecollection = self._collection()
		try:
			thecollection.insert(bson.son.SON({'collection': collection_name, 'counter': initial}))
		except pymongo.errors.DuplicateKeyError:
			pass			

	@session_wrapper_context()
	def counter_next(self, collection_name):
		db_session = session_access_context()
		counters_collection = self._collection()
		counter = counters_collection.find_and_modify(
			bson.son.SON({'collection': collection_name}),
			bson.son.SON({'$inc': {'counter': 1}}),
		)
		return counter.get('counter', 0)

