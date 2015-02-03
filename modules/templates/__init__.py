# -*- coding: utf-8 -*-

import jinja2

import config
import modules.data.cache as mod

class BytecodeCache(jinja2.BytecodeCache):
	@mod.session_wrapper_context()
	def load_bytecode(self, bucket):
		db_session = mod.session_access_context()
		try:
			value = db_session.get('template##cache##%s' % bucket.key)
		except mod.redis.RedisError:
			value = None
		if value is not None:
			bucket.bytecode_from_string(value)

	@mod.session_wrapper_context()
	def dump_bytecode(self, bucket):
		db_session = mod.session_access_context()
		value = bucket.bytecode_to_string()
		try:
			db_session.set('template##cache##%s' % bucket.key, value)
		except mod.redis.RedisError:
			pass

	@mod.session_wrapper_context()
	def clear(self):
		pass

class Template(jinja2.Template):
	def new_context(self, vars=None, shared=False, locals=None):
		def safe_strings(value):
			if isinstance(value, str):
				return value.decode('utf-8')
			return value
		if isinstance(vars, dict):
			vars = dict(((safe_strings(k), safe_strings(v)) for k, v in vars.iteritems()))
		if isinstance(shared, dict):
			shared = dict(((safe_strings(k), safe_strings(v)) for k, v in shared.iteritems()))
		if isinstance(locals, dict):
			locals = dict(((safe_strings(k), safe_strings(v)) for k, v in locals.iteritems()))
		return super(Template, self).new_context(vars, shared, locals)

class Environment(jinja2.Environment):
	def __init__(self, template_loader):
		super(Environment, self).__init__(
			extensions=['jinja2.ext.loopcontrols', 'jinja2.ext.do', 'jinja2.ext.i18n', 'jinja2.ext.with_'],
			bytecode_cache=BytecodeCache(),
			loader=template_loader,
		)
		self.globals['config'] = config
		from util.values import build_url as _url
		self.filters['url'] = lambda kwargs: _url(**kwargs)
		import json
		self.filters['json'] = lambda arg: json.dumps(arg)
		import datetime
		def filter_datetime(arg, fmt):
			if isinstance(arg, datetime.datetime):
				return arg.strftime(fmt)
			else:
				return 'Not a datetime'
		self.filters['datetime'] = filter_datetime
		self.template_class = Template

