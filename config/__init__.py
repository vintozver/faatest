# -*- coding: utf-8 -*-

import os
import os.path
basedir = os.getcwd()

import ConfigParser
parser = ConfigParser.RawConfigParser()
parser.read(os.path.join(basedir, 'config.txt'))

def _import_sub():
	def inject(module):
		try:
			__import__(module)
		except ImportError, err:
			return
		module = sys.modules[module]
		if partition in globals():
			globals()[partition].__dict__.update(module.__dict__)
		else:
			globals()[partition] = module

	import sys
	partitions = ['base', 'main']
	for partition in partitions:
		inject('config.%s' % partition)
_import_sub()

