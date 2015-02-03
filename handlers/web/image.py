# -*- coding: utf-8 -*-

import httplib
import json

import modules.data.mongo as mod
import modules.data.mongo.ground_school as mod_GS

import handlers.ext.static

from handlers.ext.paramed_cgi import HandlerError as _base_error
class HandlerError(_base_error):
	pass

class ParameterFallback(HandlerError):
	pass

from handlers.ext.paramed_cgi import Handler as _base
class Handler(_base):
	def by_id(self, ImageID):
		try:
			image_item = mod_GS.QuestionImage.get_by_id(ImageID)
		except mod_GS.QuestionImage._ErrorNotFound:
			raise HandlerError('Questions.Images.ImageID not found', ImageID)
		return image_item

	def by_ids(self, QuestionID, ImageID):
		try:
			question_item = mod_GS.Question.get_by_id(QuestionID)
		except mod_GS.Question._ErrorNotFound:
			raise HandlerError('Questions.QuestionID not found', QuestionID)
		images = question_item.get('Images', [])
		images = filter(lambda image_item: image_item['ID'] == ImageID, images)
		if images:
			return images[0]
		else:
			raise HandlerError('Questions.Images.ID not found', QuestionID, ImageID)

	@mod.session_wrapper_context()
	def __call__(self):
		self.req.setHeader('Cache-Control', 'public, no-cache')

		try:
			try:
				QuestionID = self.cgi_params.param_get('QuestionID')
			except self.cgi_params.NotFoundError:
				raise ParameterFallback('Missing mandatory parameter', 'QuestionID')
			try:
				QuestionID = int(QuestionID)
			except TypeError:
				raise HandlerError('Invalid mandatory parameter', 'QuestionID')
			except ValueError:
				raise HandlerError('Invalid mandatory parameter', 'QuestionID')

			try:
				ImageID = self.cgi_params.param_get('ImageID')
			except self.cgi_params.NotFoundError:
				raise ParameterFallback('Missing mandatory parameter', 'ImageID')
			try:
				ImageID = int(ImageID)
			except TypeError:
				raise HandlerError('Invalid mandatory parameter', 'ImageID')
			except ValueError:
				raise HandlerError('Invalid mandatory parameter', 'ImageID')

			image_item = self.by_ids(QuestionID, ImageID)
		except ParameterFallback:
			try:
				ImageID = self.cgi_params.param_get('ID')
			except self.cgi_params.NotFoundError:
				raise HandlerError('Missing mandatory parameter', 'ID')
			try:
				ImageID = int(ImageID)
			except TypeError:
				raise HandlerError('Invalid mandatory parameter', 'ID')
			except ValueError:
				raise HandlerError('Invalid mandatory parameter', 'ID')

			image_item = self.by_id(ImageID)

		if image_item != None:
			self.req.setHeader('Content-Type', handlers.ext.static.Handler(self.req).mimetype(image_item.get('FileName', 'untitled.bin')))
			self.req.setHeader('Content-Length', len(image_item.BinImage))

			self.req.setResponseCode(httplib.OK, httplib.responses[httplib.OK])
			self.req.write(image_item.BinImage)
		else:
			self.req.setResponseCode(httplib.NOT_FOUND, httplib.responses[httplib.NOT_FOUND])
			self.req.setHeader('Content-Type', 'text/plain; charset=utf-8')
			self.req.write('Requested entity not found')

