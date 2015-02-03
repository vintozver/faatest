# -*- coding: utf-8 -*-

import bson.son
import pymongo

import config
import modules.data.mongo as mod

class Group(mod.DataObject):
	class _GenericError(mod.DataObject._Error):
		pass
	class _ErrorNotFound(_GenericError):
		pass

	def __getattribute__(self, key):
		if key in ['GroupID', 'GroupName', 'GroupAbbr', 'LastMod']:
			return self[key]
		else:
			return mod.DataObject.__getattribute__(self, key)

	@classmethod
	@mod.session_wrapper_context()
	def _collection(cls):
		db_session = mod.session_access_context()
		thecollection = db_session[config.main.db_mongo['name']]['Groups']
		return thecollection

	@classmethod
	@mod.session_wrapper_context()
	def schema_init(cls):
		db_session = mod.session_access_context()
		thecollection = cls._collection()
		thecollection.ensure_index('GroupID', unqiue=True)

	@classmethod
	@mod.session_wrapper_context()
	def get_by_id(cls, GroupID):
		thecollection = cls._collection()
		obj_data = thecollection.find_one(bson.son.SON({'GroupID': GroupID}))
		if obj_data == None:
			raise cls._ErrorNotFound()
		return cls.create_from_data(obj_data)

	@classmethod
	@mod.session_wrapper_context()
	def get_list(cls):
		thecollection = cls._collection()
		objs_data = thecollection.find(bson.son.SON({}), sort=[('GroupID', pymongo.ASCENDING)])
		objs = list()
		for obj_data in objs_data:
			objs.append(cls.create_from_data(obj_data))
		return objs

class Test(mod.DataObject):
	class _GenericError(mod.DataObject._Error):
		pass
	class _ErrorNotFound(_GenericError):
		pass

	def __getattribute__(self, key):
		if key in ['GroupID', 'TestID', 'TestName', 'TestAbbr', 'SortBy', 'LastMod']:
			return self[key]
		else:
			return mod.DataObject.__getattribute__(self, key)

	@classmethod
	@mod.session_wrapper_context()
	def _collection(cls):
		db_session = mod.session_access_context()
		thecollection = db_session[config.main.db_mongo['name']]['Tests']
		return thecollection

	@classmethod
	@mod.session_wrapper_context()
	def schema_init(cls):
		db_session = mod.session_access_context()
		thecollection = cls._collection()
		thecollection.ensure_index('TestID', unqiue=True)

	@classmethod
	@mod.session_wrapper_context()
	def get_by_id(cls, TestID):
		thecollection = cls._collection()
		obj_data = thecollection.find_one(bson.son.SON({'TestID': TestID}))
		if obj_data == None:
			raise cls._ErrorNotFound()
		return cls.create_from_data(obj_data)

	@classmethod
	@mod.session_wrapper_context()
	def get_list_by_group_id(cls, GroupID):
		thecollection = cls._collection()
		objs_data = thecollection.find(bson.son.SON({'GroupID': GroupID}), sort=[('SortBy', pymongo.ASCENDING)])
		objs = list()
		for obj_data in objs_data:
			objs.append(cls.create_from_data(obj_data))
		return objs

class Chapter(mod.DataObject):
	class _GenericError(mod.DataObject._Error):
		pass
	class _ErrorNotFound(_GenericError):
		pass

	def __getattribute__(self, key):
		if key in ['ChapterID', 'ChapterName', 'GroupID', 'SortBy', 'LastMod']:
			return self[key]
		else:
			return mod.DataObject.__getattribute__(self, key)

	@classmethod
	@mod.session_wrapper_context()
	def _collection(cls):
		db_session = mod.session_access_context()
		thecollection = db_session[config.main.db_mongo['name']]['Chapters']
		return thecollection

	@classmethod
	@mod.session_wrapper_context()
	def schema_init(cls):
		db_session = mod.session_access_context()
		thecollection = cls._collection()
		thecollection.ensure_index('ChapterID', unqiue=True)

	@classmethod
	@mod.session_wrapper_context()
	def get_by_id(cls, ChapterID):
		thecollection = cls._collection()
		obj_data = thecollection.find_one(bson.son.SON({'ChapterID': ChapterID}))
		if obj_data == None:
			raise cls._ErrorNotFound()
		return cls.create_from_data(obj_data)

	@classmethod
	@mod.session_wrapper_context()
	def get_list_by_group_id(cls, GroupID):
		thecollection = cls._collection()
		objs_data = thecollection.find(bson.son.SON({'GroupID': GroupID}), sort=[('SortBy', pymongo.ASCENDING)])
		objs = list()
		for obj_data in objs_data:
			objs.append(cls.create_from_data(obj_data))
		return objs

class Question(mod.DataObject):
	class _GenericError(mod.DataObject._Error):
		pass
	class _ErrorNotFound(_GenericError):
		pass

	def __getattribute__(self, key):
		if key in ['QuestionID', 'QuestionText', 'ChapterID', 'SMCID', 'SourceID', 'LockAnswers', 'LastMod', 'Explanation', 'OldQID', 'LSCID']:
			return self[key]
		else:
			return mod.DataObject.__getattribute__(self, key)

	@classmethod
	@mod.session_wrapper_context()
	def _collection(cls):
		db_session = mod.session_access_context()
		thecollection = db_session[config.main.db_mongo['name']]['Questions']
		return thecollection

	@classmethod
	@mod.session_wrapper_context()
	def schema_init(cls):
		db_session = mod.session_access_context()
		thecollection = cls._collection()
		thecollection.ensure_index('QuestionID', unqiue=True)

	@classmethod
	@mod.session_wrapper_context()
	def get_by_id(cls, QuestionID):
		thecollection = cls._collection()
		obj_data = thecollection.find_one(bson.son.SON({'QuestionID': QuestionID}))
		if obj_data == None:
			raise cls._ErrorNotFound()
		return cls.create_from_data(obj_data)

class Answer(mod.DataObject):
	class _GenericError(mod.DataObject._Error):
		pass
	class _ErrorNotFound(_GenericError):
		pass

	def __getattribute__(self, key):
		if key in ['AnswerID', 'AnswerText', 'QuestionID', 'IsCorrect', 'SortBy', 'LastMod']:
			return self[key]
		else:
			return mod.DataObject.__getattribute__(self, key)

class QuestionTest(mod.DataObject):
	class _GenericError(mod.DataObject._Error):
		pass
	class _ErrorNotFound(_GenericError):
		pass

	def __getattribute__(self, key):
		if key in ['QuestionID', 'TestID', 'IsLinked', 'SortBy', 'LinkChapter', 'IsImportant']:
			return self[key]
		else:
			return mod.DataObject.__getattribute__(self, key)

	@classmethod
	@mod.session_wrapper_context()
	def _collection(cls):
		db_session = mod.session_access_context()
		thecollection = db_session[config.main.db_mongo['name']]['QuestionsTests']
		return thecollection

	@classmethod
	@mod.session_wrapper_context()
	def schema_init(cls):
		db_session = mod.session_access_context()
		thecollection = cls._collection()
		thecollection.ensure_index('QuestionID', unqiue=True)

	@classmethod
	@mod.session_wrapper_context()
	def get_by_ids(cls, TestID, QuestionID):
		thecollection = cls._collection()
		obj_data = thecollection.find_one(bson.son.SON({'TestID': TestID, 'QuestionID': QuestionID}))
		if obj_data == None:
			raise cls._ErrorNotFound()
		return cls.create_from_data(obj_data)

	@classmethod
	@mod.session_wrapper_context()
	def get_questions_by_test_id(cls, TestID):
		def _list():
			thecollection = cls._collection()
			objs_data = thecollection.find(bson.son.SON({'TestID': TestID}), sort=[('SortBy', pymongo.ASCENDING)])
			for obj_data in objs_data:
				try:
					yield Question.get_by_id(obj_data['QuestionID'])
				except Question._ErrorNotFound:
					pass
		return list(_list())

class QuestionImage(mod.DataObject):
	class _GenericError(mod.DataObject._Error):
		pass
	class _ErrorNotFound(_GenericError):
		pass

	def __getattribute__(self, key):
		if key in ['ImageID', 'ImageName', 'Desc', 'BinImage', 'SortBy']:
			return self[key]
		else:
			return mod.DataObject.__getattribute__(self, key)

	@classmethod
	@mod.session_wrapper_context()
	def get_by_id(cls, ImageID):
		thecollection = Question._collection()
		obj_data = thecollection.find_one(bson.son.SON({'Images.ImageID': ImageID}))
		if obj_data == None:
			raise cls._ErrorNotFound()
		try:
			obj_images = obj_data['Images']
		except KeyError:
			raise cls._ErrorNotFound()
		obj_images = filter(lambda obj_image: obj_image['ImageID'] == ImageID, obj_images)
		if obj_images:
			return cls.create_from_data(obj_images[0])
		else:
			raise cls._ErrorNotFound()

