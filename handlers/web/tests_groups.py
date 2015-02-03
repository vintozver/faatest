# -*- coding: utf-8 -*-

import httplib
import json
import bson
import pymongo

import config
import modules.data.mongo as mod
import modules.data.mongo.ground_school as mod_GS

from handlers.ext.paramed_cgi import HandlerError as _base_error
class HandlerError(_base_error):
	pass

from handlers.ext.paramed_cgi import Handler as _base
class Handler(_base):
	def Groups(self):
		items = mod_GS.Group.get_list()
		return {'Groups': [{'GroupID': item['GroupID'], 'GroupName': item['GroupName'], 'GroupAbbr': item['GroupAbbr']} for item in items]}

	@mod.session_wrapper_context()
	def Tests(self, GroupID):
		try:
			group_item = mod_GS.Group.get_by_id(GroupID)
		except mod_GS.Group._ErrorNotFound:
			raise HandlerError('Groups.GroupID not found', GroupID)
		tests_items = mod_GS.Test.get_list_by_group_id(GroupID)
		return {
			'Group': {
				'GroupID': group_item['GroupID'],
				'GroupName': group_item['GroupName'],
				'GroupAbbr': group_item['GroupAbbr'],
			},
			'Tests': [
				{
					'TestID': test_item['TestID'],
					'TestName': test_item['TestName'],
					'TestAbbr': test_item['TestAbbr'],
				}
				for test_item in tests_items
			],
		}

	def __call__(self):
		try:
			group_list = bool(self.cgi_params.param_get('Groups'))
		except self.cgi_params.NotFoundError:
			group_list = False

		if group_list:
			result = self.Groups()
		else:
			try:
				GroupID = self.cgi_params.param_get('GroupID')
			except self.cgi_params.NotFoundError:
				raise HandlerError('Missing mandatory parameter', 'GroupID')
			try:
				GroupID = int(GroupID)
			except TypeError:
				raise HandlerError('Invalid mandatory parameter', 'GroupID')
			except ValueError:
				raise HandlerError('Invalid mandatory parameter', 'GroupID')
			result = self.Tests(GroupID)

		content = json.dumps(result)
		self.req.setResponseCode(httplib.OK, httplib.responses[httplib.OK])
		self.req.setHeader('Cache-Control', 'public, no-cache')
		self.req.setHeader('Content-Type', 'application/json; charset=utf-8')
		self.req.write(content)

