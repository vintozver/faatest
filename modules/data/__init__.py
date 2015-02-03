# -*- coding: utf-8 -*-

import config

class dataobject(object):
	__attributes__ = ()

	def __init__(self, **kwargs):
		for kwarg_key, kwarg_value in kwargs.iteritems():
			if kwarg_key in self.__attributes__:
				setattr(self, kwarg_key, kwarg_value)
			else:
				raise AttributeError('Attribute "%s" is not allowed for this dataobject' % kwarg_key)

	def assign(self, obj):
		for attribute in self.__attributes__:
			setattr(self, attribute, getattr(obj, attribute))

	@staticmethod
	def _lookup_dataobject_class(cls):
		checkcls = cls
		while checkcls != dataobject:
			if issubclass(checkcls, dataobject):
				checkcls = checkcls.__base__
			else:
				break
		if checkcls == dataobject:
			return cls

		for item in cls.__bases__:
			checkcls = dataobject._lookup_dataobject_class(item)
			if checkcls:
				return checkcls
		return None

	def copy(self):
		cls = dataobject._lookup_dataobject_class(self.__class__)
		obj = cls()
		obj.assign(self)
		return obj

