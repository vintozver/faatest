# -*- coding: utf-8 -*-

import os.path
import jinja2

import modules.templates as mod

import config

class TemplateLoader(jinja2.BaseLoader):
	def get_source(self, environment, template):
		template_path = os.path.join(config.main.basedir, 'templates', '%s.tmpl' % template.replace('.', '/'))

		mtime = os.path.getmtime(template_path)
		def uptodate():
			try:
				return os.path.getmtime(template_path) == mtime
			except OSError:
				return False

		try:
			return open(template_path).read().decode('utf-8'), 'Template: %s' % template, uptodate
		except OSError:
			raise TemplateNotFound(template)

def TemplateFactory(xtmpl_name):
	try:
		return mod.Environment(TemplateLoader()).get_template(xtmpl_name)
	except jinja2.TemplateNotFound, err:
		raise TemplateError('Template not imported', xtmpl_name)

class TemplateError(Exception):
	pass

__all__ = ['TemplateFactory', 'TemplateError']

