# Decorators for request handlers and important functions

import CGI
import errors

def public(method):
	method.public = True
	return method

def authenticated(method):
	def wrapper(self, *args, **kwargs):
		if self.req.Session.id_user != None:
			return method(self, *args, **kwargs)
		else:
			raise errors.AuthenticationError('Method requires authentication')
	wrapper.authenticated = True
	return wrapper

