# -*- coding: utf-8 -*-

import config.base

import os.path

product_name = config.base.product_name
product_description = config.base.product_description

basedir = config.base.basedir

port_base = config.base.port_base
port_web = port_base + 1
port_db_mongo = port_base + 7
port_db_cache = port_base + 8

db_mongo = dict()
try:
	try:
		db_mongo['local_instance'] = config.base.parser.getboolean('db_mongo', 'local_instance')
	except config.base.ConfigParser.NoOptionError:
		db_mongo['local_instance'] = True
	try:
		db_mongo['name'] = config.base.parser.get('db_mongo', 'name')
	except config.base.ConfigParser.NoOptionError:
		db_mongo['name'] = 'dropzone'
	if db_mongo['local_instance']:
		db_mongo['dir'] = 'run/mongo'
		try:
			db_mongo['journal'] = config.base.parser.getboolean('db_mongo', 'journal')
		except config.base.ConfigParser.NoOptionError:
			db_mongo['journal'] = True
		db_mongo['host'] = 'localhost'
		db_mongo['port'] = port_db_mongo
		db_mongo['user'] = None
		db_mongo['password'] = None
	else:
		try:
			db_mongo['host'] = config.base.parser.get('db_mongo', 'host')
		except config.base.ConfigParser.NoOptionError:
			db_mongo['host'] = 'localhost'
		try:
			db_mongo['port'] = config.base.parser.getint('db_mongo', 'port')
		except config.base.ConfigParser.NoOptionError:
			db_mongo['port'] = 27017
		try:
			db_mongo['user'] = config.base.parser.get('db_mongo', 'user')
		except config.base.ConfigParser.NoOptionError:
			db_mongo['user'] = None
		try:
			db_mongo['password'] = config.base.parser.get('db_mongo', 'password')
		except config.base.ConfigParser.NoOptionError:
			db_mongo['password'] = None
except config.base.ConfigParser.NoSectionError:
	db_mongo['local_instance'] = True
	db_mongo['name'] = 'dropzone'
	db_mongo['dir'] = 'run/mongo'
	db_mongo['journal'] = True
	db_mongo['host'] = 'localhost'
	db_mongo['port'] = port_db_mongo
	db_mongo['user'] = None
	db_mongo['password'] = None

db_cache = dict()
try:
	try:
		db_cache['local_instance'] = config.base.parser.getboolean('db_cache', 'local_instance')
	except config.base.ConfigParser.NoOptionError:
		db_cache['local_instance'] = True
	try:
		db_cache['index'] = config.base.parser.getint('db_cache', 'index')
	except config.base.ConfigParser.NoOptionError:
		db_cache['index'] = 0
	try:
		db_cache['password'] = config.base.parser.get('db_cache', 'password')
	except config.base.ConfigParser.NoOptionError:
		db_cache['password'] = None
	if db_cache['local_instance']:
		db_cache['dir'] = 'run/cache'
		db_cache['host'] = 'localhost'
		db_cache['port'] = port_db_cache
	else:
		try:
			db_cache['host'] = config.base.parser.get('db_cache', 'host')
		except config.base.ConfigParser.NoOptionError:
			db_cache['host'] = 'localhost'
		try:
			db_cache['port'] = config.base.parser.getint('db_cache', 'port')
		except config.base.ConfigParser.NoOptionError:
			db_cache['port'] = 6379
except config.base.ConfigParser.NoSectionError:
	db_cache['local_instance'] = True
	db_cache['index'] = 0
	db_cache['password'] = None
	db_cache['dir'] = 'run/cache'
	db_cache['host'] = 'localhost'
	db_cache['port'] = port_db_cache

log_dir = 'run/log'

domain_root = config.base.domain_root
domain_static = 'static.%s' % domain_root
domain_internal = 'internal.%s' % domain_root
domain_www = 'www.%s' % domain_root
domain_m = 'm.%s' % domain_root

mail_server_smtp = 'localhost'
mail_server_user = None
mail_server_password = None

email_admin = 'Адмиинистратор DROPZONE.BY <admin@dropzone.by>'
email_webservice = 'Веб-робот DROPZONE.BY <webservice@dropzone.by>'

timezone = 'Europe/Minsk'

pidfile_dir = 'run/pid'
pidfile_web = 'web.pid'
pidfile_db_mongo = 'db_mongo.pid'
pidfile_db_cache = 'db_cache.pid'
pidfile_defer = 'defer.pid'

