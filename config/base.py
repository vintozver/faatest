# -*- coding: utf-8 -*-

import os.path

import config

product_name = 'FAA Test'
product_description = 'Testing to cool people'

basedir = config.basedir

import ConfigParser
parser = ConfigParser.RawConfigParser()
parser.read(os.path.join(basedir, 'config.txt'))
try:
	port_base = parser.getint('base', 'port')
except ConfigParser.NoOptionError:
	port_base = 10000
except ConfigParser.NoSectionError:
	port_base = 10000

domain_root = 'test.dropzone.by'

