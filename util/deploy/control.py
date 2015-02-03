#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys
import os
import os.path
import re
import signal
import time

import subprocess
import lockfile
import daemon


import config


class ControlError(Exception):
	pass


class ServiceAction(object):
	def __init__(self, name):
		self.name = name

	def __call__(self, method):
		method.action_name = self.name
		return method

class Service(object):
	def __init__(self):
		self.action_map = dict()
		for attr_name in dir(self):
			try:
				attr = getattr(self, attr_name)
			except AttributeError:
				continue
			if callable(attr) and hasattr(attr, 'action_name'):
				self.action_map[attr.action_name] = attr

	def __call__(self, action, *args, **kwargs):
		try:
			action_method = self.action_map[action]
		except KeyError:
			try:
				action_method = getattr(self, 'action_%s' % action)
			except AttributeError:
				raise ControlError('Action is not implemented', action)
			if not callable(action_method):
				raise ControlError('Action is not implemented', action)
		return action_method(*args, **kwargs)

class OneInstanceService(Service):
	def pidfile_path(self):
		raise NotImplementedError

	def worker(self):
		raise NotImplementedError

	def worker_kill(self, signum, frame):
		raise NotImplementedError

	def pidfile_create(self):
		try:
			pidfile = open(self.pidfile_path(), 'w+b')
			try:
				pidfile.write('%d' % os.getpid())
			finally:
				pidfile.close()
		except OSError:
			raise ControlError(type(self), 'Cannot create pid file')

	def pidfile_destroy(self):
		try:
			os.unlink(self.pidfile_path())
		except OSError:
			pass

	def pid(self):
		try:
			pidfile = open(self.pidfile_path(), 'rb')
			try:
				pidstr = pidfile.read()
				try:
					pid = int(pidstr)
				except TypeError:
					raise ControlError(type(self), 'Incorrect pid file contents')
				except ValueError:
					raise ControlError(type(self), 'Incorrect pid file contents')
				return pid
			finally:
				pidfile.close()
		except IOError:
			raise ControlError(type(self), 'No pid file or service is not running')

	@ServiceAction('start')
	def action_start(self):
		lock = lockfile.FileLock(self.pidfile_path())
		if lock.is_locked():
			raise ControlError(type(self), 'Service is already running')

		context = daemon.DaemonContext(
			working_directory=config.main.basedir,
			umask=0o022,
		)
		context.signal_map = {
			signal.SIGTERM: self.worker_kill,
			signal.SIGHUP: self.worker_kill,
			signal.SIGINT: self.worker_kill,
		}
		with context:
			self.worker()

	@ServiceAction('stop')
	def action_stop(self):
		try:
			os.kill(self.pid(), signal.SIGTERM)
		except OSError, err:
			raise ControlError(type(self), 'Failed to kill the service process')

		lock = lockfile.FileLock(self.pidfile_path())
		timeout = 10
		while lock.is_locked():
			if timeout > 0:
				timeout = timeout - 1
			else:
				ControlError(type(self), 'Failed to wait for the service process')


class Web(OneInstanceService):
	def pidfile_path(self):
		return os.path.join(config.main.basedir, config.main.pidfile_dir, config.main.pidfile_web)

	def worker(self):
		lock = lockfile.FileLock(self.pidfile_path())
		lock.acquire(0)
		try:
			self.pidfile_create()

			try:
				import prctl
				prctl.set_proctitle('CONTROL/web/%s' % config.main.product_name)
			except ImportError:
				pass

			import multiprocessing
			try:
				proc_count = multiprocessing.cpu_count()
			except NotImplementedError:
				proc_count = 1

			env = os.environ
			env['PYTHONPATH'] = config.main.basedir
			params = ['gunicorn', '--workers=%d' % (proc_count + 1), '--max-requests=1000',
				'--bind=:%d' % config.main.port_web,
				'--worker-class=gevent', 'util.web.publisher:Request',
			]
			stdin = open('/dev/null', 'r')
			stdout = open(os.path.join(config.main.basedir, config.main.log_dir, 'service_web.out'), 'a+')
			stderr = open(os.path.join(config.main.basedir, config.main.log_dir, 'service_web.err'), 'a+')
			self.web_process = subprocess.Popen(params,
				stdin=stdin, stdout=stdout, stderr=stderr,
				cwd=config.main.basedir,
				env=env,
			)
			stdin.close()
			stdout.close()
			stderr.close()
			self.web_process.wait()
			del self.web_process
		finally:
			self.pidfile_destroy()
			lock.release()

	def worker_kill(self, signum, frame):
		try:
			os.kill(self.web_process.pid, signum)
		except OSError:
			pass

	@ServiceAction('restart')
	def action_restart(self):
		try:
			os.kill(self.pid(), signal.SIGHUP)
		except OSError, err:
			raise ControlError('Web', 'Failed to reload the service process')

class DbMongo(OneInstanceService):
	def pidfile_path(self):
		return os.path.join(config.main.basedir, config.main.pidfile_dir, config.main.pidfile_db_mongo)

	def worker(self):
		lock = lockfile.FileLock(self.pidfile_path())
		lock.acquire(0)
		try:
			self.pidfile_create()

			try:
				import prctl
				prctl.set_proctitle('CONTROL/db_mongo/%s' % config.main.product_name)
			except ImportError:
				pass

			env = os.environ
			params = ['mongod', '--nohttpinterface', '--auth', '--logpath', os.path.join(config.main.basedir, config.main.log_dir, 'service_db_mongo.log'), '--logappend', '--dbpath', config.main.db_mongo['dir'], '--port', str(config.main.db_mongo['port'])]
			if (not config.stage or config.stage == ('live', )) and config.main.db_mongo['journal']:
				params.append('--journal')
			stdin = open('/dev/null', 'r')
			stdout = open('/dev/null', 'a+')
			stderr = open('/dev/null', 'a+')
			self.db_mongo_process = subprocess.Popen(params, stdin=stdin, stdout=stdout, stderr=stderr, cwd=config.main.basedir, env=env)
			stdin.close()
			stdout.close()
			stderr.close()
			self.db_mongo_process.wait()
			del self.db_mongo_process
		finally:
			self.pidfile_destroy()
			lock.release()

	def worker_kill(self, signum, frame):
		try:
			os.kill(self.db_mongo_process.pid, signum)
		except OSError:
			pass

	@ServiceAction('schema-update')
	def schema_update(self):
		pass


class DbCache(OneInstanceService):
	def pidfile_path(self):
		return os.path.join(config.main.basedir, config.main.pidfile_dir, config.main.pidfile_db_cache)

	def worker(self):
		lock = lockfile.FileLock(self.pidfile_path())
		lock.acquire(0)
		try:
			self.pidfile_create()

			try:
				import prctl
				prctl.set_proctitle('CONTROL/db_cache/%s' % config.main.product_name)
			except ImportError:
				pass

			env = os.environ
			params = ['redis-server', '-']
			stdin = open('/dev/null', 'r')
			stdout = open(os.path.join(config.main.basedir, config.main.log_dir, 'service_cache.out'), 'a+')
			stderr = open(os.path.join(config.main.basedir, config.main.log_dir, 'service_cache.err'), 'a+')
			self.db_cache_process = subprocess.Popen(params, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, cwd=config.main.basedir, env=env)
			self.db_cache_process.stdin.write('\
port %(port)d\n\
timeout 300\n\
\
loglevel notice\n\
logfile stdout\n\
\
databases 16\n\
\
save 900 1\n\
save 300 10\n\
save 60 10000\n\
\
rdbcompression yes\n\
\
dir %(dir)s\n\
dbfilename dump.rdb\n\
\
slave-serve-stale-data yes\n\
\
appendonly no\n\
appendfsync everysec\n\
no-appendfsync-on-rewrite no\n\
vm-enabled no\n\
\
vm-swap-file redis.swap\n\
\
vm-max-memory 0\n\
vm-page-size 32\n\
vm-pages 134217728\n\
vm-max-threads 4\n\
hash-max-zipmap-entries 512\n\
hash-max-zipmap-value 64\n\
list-max-ziplist-entries 512\n\
list-max-ziplist-value 64\n\
set-max-intset-entries 512\n\
activerehashing yes\n\
' % {'port': config.main.db_cache['port'], 'dir': os.path.join(config.main.basedir, config.main.db_cache['dir'])})
			self.db_cache_process.stdin.close()
			stdout.close()
			stderr.close()
			self.db_cache_process.wait()
			del self.db_cache_process
		finally:
			self.pidfile_destroy()
			lock.release()

	def worker_kill(self, signum, frame):
		try:
			os.kill(self.db_cache_process.pid, signum)
		except OSError:
			pass


class Defer(OneInstanceService):
	def pidfile_path(self):
		return os.path.join(config.main.basedir, config.main.pidfile_dir, config.main.pidfile_defer)

	def worker(self):
		lock = lockfile.FileLock(self.pidfile_path())
		lock.acquire(0)
		try:
			self.pidfile_create()

			try:
				import prctl
				prctl.set_proctitle('CONTROL/defer/%s' % config.main.product_name)
			except ImportError:
				pass

			env = os.environ
			env['PYTHONPATH'] = config.main.basedir
			params = ['celery', 'worker', '--pool=gevent', '--loader=util.defer.Loader',
				'--logfile=logs/defer.log', '--loglevel=INFO',
			]
			stdin = open('/dev/null', 'r')
			stdout = open(os.path.join(config.main.basedir, config.main.log_dir, 'service_defer.out'), 'a+')
			stderr = open(os.path.join(config.main.basedir, config.main.log_dir, 'service_defer.err'), 'a+')
			self.defer_process = subprocess.Popen(params, stdin=stdin, stdout=stdout, stderr=stderr, cwd=config.main.basedir, env=env)
			stdin.close()
			stdout.close()
			stderr.close()
			self.defer_process.wait()
			del self.defer_process
		finally:
			self.pidfile_destroy()
			lock.release()

	def worker_kill(self, signum, frame):
		try:
			os.kill(self.defer_process.pid, signum)
		except OSError:
			pass


SERVICE_MAPPING = {
	'db_mongo': DbMongo,
	'db_cache': DbCache,
	'defer': Defer,
	'web': Web,
}


if __name__ == '__main__':
	import argparse
	argparser = argparse.ArgumentParser()
	argparser.add_argument('--service', dest='service', default='all', help='service')
	argparser.add_argument('--action', dest='action', default='kick', help='action applied to servers pool')
	args = argparser.parse_args()

	try:
		try:
			service_class = SERVICE_MAPPING[args.service]
		except KeyError:
			raise ControlError('Invalid service', args.service)
		service_class()(args.action)
	except ControlError, err:
		sys.stderr.write('ERROR: %s\n' % repr(err.args))

