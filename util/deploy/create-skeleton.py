#!/usr/bin/env python

import sys
import os

import config

def makedirs_silent(*args, **kwargs):
	try:
		os.makedirs(*args, **kwargs)
	except os.error:
		pass

def do_base():
	makedirs_silent(os.path.join(config.main.basedir, config.main.log_dir))
	makedirs_silent(os.path.join(config.main.basedir, config.main.pidfile_dir))
	makedirs_silent(os.path.join(config.main.basedir, config.main.cache_dir))
if __name__ == '__main__':
	do_base()

def do_db_mongo():
	makedirs_silent(os.path.join(config.main.basedir, config.main.db_mongo_dir))
if __name__ == '__main__':
	do_db_mongo()

