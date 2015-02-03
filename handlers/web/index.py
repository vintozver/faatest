# -*- coding: utf-8 -*-

import httplib

import modules.templates.filesystem as mod_tmpl_fs

from handlers.ext.paramed_cgi import HandlerError as _base_error
class HandlerError(_base_error):
	pass

from handlers.ext.paramed_cgi import Handler as _base
class Handler(_base):
	def __call__(self):
		tmpl_args = dict()
		content = mod_tmpl_fs.TemplateFactory('index').render(tmpl_args)
		self.req.setResponseCode(httplib.OK, httplib.responses[httplib.OK])
		self.req.setHeader('Cache-Control', 'public, no-cache')
		self.req.setHeader('Content-Type', 'text/html; charset=utf-8')
		self.req.write(content)

