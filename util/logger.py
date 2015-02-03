# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os.path
import datetime
import logging


class NullStream(logging.Handler):
	def read(self, *args, **kwargs):
		pass
	def write(self, *args, **kwargs):
		pass
	def flush(self):
		pass

logging.basicConfig(
	stream = NullStream(),
	level = logging.DEBUG,
	format = '%(asctime)s - %(levelname)s - %(message)s',
	datefmt = '%Y-%m-%d %H:%M:%S',
)


class Logger(object):
	def __init__(self, req):
		self.req = req
	
	def traceback(self, err_type, err_value, err_tb):
		import traceback
		tb = reduce(
			lambda line_up, line_down: line_up + '\n' + line_down,
			map(
				lambda item: '%s: %s' % (item[0], item[1]),
				traceback.extract_tb(err_tb)
			)
		)
		logger = logging.getLogger('traceback')
		logger.info('''Ошибка
Тип: %(type)s
Значение: %(value)s
Трасса:
%(tb)s

''' % {'type': err_value.__class__.__name__, 'value': str(err_value), 'tb': tb}
		)

