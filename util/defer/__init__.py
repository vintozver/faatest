# -*- coding: utf-8 -*-


import config

from celery.utils import uuid

import celery.loaders.app
class Loader(celery.loaders.app.AppLoader):
	def read_configuration(self):
		self.configured = True
		return {
			'CELERY_IMPORTS': ('util.defer', 'handlers.defer', ),
			'CELERY_ENABLE_UTC': True,
			'CELERY_DISABLE_RATE_LIMITS': True,  # required for gevent backend: https://github.com/ask/celery/issues/425
			'BROKER_URL': 'redis://%s:%s/%s' % ('localhost', config.main.port_db_cache, 1),
			'CELERY_RESULT_BACKEND': 'redis',
			'CELERY_REDIS_HOST': 'localhost',
			'CELERY_REDIS_PORT': config.main.port_db_cache,
			'CELERY_REDIS_DB': 1,
		}

import celery.app
class App(celery.app.App):
	loader_cls = Loader

the_app = App()

Task = the_app.Task

