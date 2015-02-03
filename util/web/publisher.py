#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import gevent.monkey
gevent.monkey.patch_all()

import sys
import os
import logging
import traceback

import util.CGI.request
import util.logger

import config

logger = logging.getLogger('traceback')
handler = logging.FileHandler(os.path.join(config.main.basedir, config.main.log_dir, 'traceback_web.log'))
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)

class Request(util.CGI.request.Request):
	def __call__(self):
		logger_obj = util.logger.Logger(self)
		try:
			self.setHeader('Server', 'UltraFast/%s web' % config.main.product_name)

			import handlers.web
			return handlers.web.Handler(self)()
		except:
			err_type, err_value, err_tb = sys.exc_info()
			logger_obj.traceback(err_type, err_value, err_tb)


if __name__ == '__main__':
	import gevent
	import gevent.baseserver
	listener = gevent.baseserver._tcp_listener(('', config.main.port_web), reuse_addr=True)

	def service(listener_instance):
		from gevent.pywsgi import WSGIServer
		server_kwargs = {}
		if not config.stage or config.stage == ('live', ):
			server_kwargs['log'] = None
		server = WSGIServer(listener_instance, Request, **server_kwargs)
		import signal
		def signal_newhandler(signum, frame):
			signal.signal(signal.SIGTERM, signal_oldhandler)
			server.stop()
		signal_oldhandler = signal.signal(signal.SIGTERM, signal_newhandler)
		server.serve_forever()


	import multiprocessing
	try:
		proc_count = multiprocessing.cpu_count()
	except NotImplementedError:
		proc_count = 4

	processes = []
	for proc_index in range(proc_count):
		process = multiprocessing.Process(target=service, args=(listener, ))
		process.start()
		processes.append(process.pid)

	import signal
	def signal_newhandler(signum, frame):
		signal.signal(signal.SIGTERM, signal_oldhandler)
		for pid in processes:
			os.kill(pid, signum)
	signal_oldhandler = signal.signal(signal.SIGTERM, signal_newhandler)

	while True:
		try:
			os.waitpid(0, 0)
		except OSError:
			break

