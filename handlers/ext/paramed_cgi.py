# -*- coding: utf-8 -*-

from util.handler import HandlerError as _base_error
class HandlerError(_base_error):
	pass

from util.handler import Handler as _base
class Handler(_base):
	def __init__(self, req):
		super(Handler, self).__init__(req)

		from util.CGI.params import Params as CGI_Params
		try:
			self.cgi_params = CGI_Params(self.req, True, self.req.method == 'POST')
		except CGI_Params.ParseError:
			raise HandlerError('Error parsing request params')

