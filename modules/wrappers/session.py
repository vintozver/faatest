# $Id: session.py,v 2e7239f5b2e0 2010/03/20 18:29:22 jribbens $

import hmac, Cookie, random, fcntl
import os
import errno
import re
import time
import datetime
try:
	import hashlib
	sha = hashlib.sha1
	shanew = hashlib.sha1
except ImportError:
	import sha
	shanew = sha.new
try:
	import cPickle as pickle
except ImportError:
	import pickle


class Error(Exception):
	pass


class Session(dict):
	def _make_hash(self, sid, secret):
		"""Create a hash for 'sid'
		
		This function may be overridden by subclasses."""
		return hmac.new(secret, sid, sha).hexdigest()[:8]

	def _create(self, secret):
		"""Create a new session ID and, optionally hash
		
		This function must insert the new session ID (which must be 8 hexadecimal
		characters) into self["id"].

		It may optionally insert the hash into self["hash"]. If it doesn't, then
		_make_hash will automatically be called later.

		This function may be overridden by subclasses.
		"""
		rnd = str(time.time()) + str(random.random()) + str(hash(self._req))
		self["id"] = shanew(rnd).hexdigest()[:8]

	def _load(self):
		"""Load the session dictionary from somewhere
		
		This function may be overridden by subclasses.
		It should return 1 if the load was successful, or 0 if the session could
		not be found. Any other type of error should raise an exception as usual."""
		return 1

	def save(self):
		"""Save the session dictionary to somewhere
		
		This function may be overridden by subclasses."""
		pass

	def tidy():
		pass
	tidy = staticmethod(tidy)

	def __init__(self, req, secret, cookie="sid", root="",
		sid=None, shash=None, secure=0, domain=None, expiration=None):
		dict.__init__(self)
		self["id"] = None
		self._req = req
		self.relocated = 0
		self.new = 0
		
		# try and determine existing session id
		
		if sid is not None:
			self["id"] = sid
			if shash is None:
				self["hash"] = self._make_hash(self["id"], secret)
			else:
				self["hash"] = shash
				if self["hash"] != self._make_hash(self["id"], secret):
					self["id"] = None

		if cookie and self._req.getCookie(cookie) != None:
			self["id"] = self._req.getCookie(cookie)[:8]
			self["hash"] = self._req.getCookie(cookie)[8:]
			if self["hash"] != self._make_hash(self["id"], secret):
				self["id"] = None

		# try and load the session

		if self["id"] is not None:
			if not self._load():
				self["id"] = None

		# if no session was available and loaded, create a new one

		if self["id"] is None:
			if "hash" in self:
				del self["hash"]
			self.created = time.time()
			self.new = 1
			self._create(secret)
			if "hash" not in self:
				self["hash"] = self._make_hash(self["id"], secret)
			if cookie:
				self._req.addCookie(cookie, self["id"] + self["hash"], expires=expiration, domain=domain, path=(root + "/"), secure=bool(secure))


class MemorySession(Session):
	_sessions = {}

	def _create(self, secret):
		while 1:
			Session._create(self, secret)
			if self["id"] in self._sessions:
				continue
			self._sessions[self["id"]] = {"created": self.created,
				"updated": self.created, "data": {}}
			break
	
	def _load(self):
		try:
			sess = self._sessions[self["id"]]
		except KeyError:
			return 0
		self.created = sess["created"]
		self.update(sess["data"])
		return 1

	def save(self):
		sess = self._sessions[self["id"]]
		sess["updated"] = time.time()
		sess["data"] = self.copy()

	def tidy(cls, max_idle=0, max_age=0):
		now = time.time()
		for k in cls._sessions:
			if (max_age and k["created"] < now - max_age) or \
				(max_idle and k["updated"] < now - max_idle):
				del cls._sessions[k]
	tidy = classmethod(tidy)


class FileSession(Session):
	def _create(self, secret):
		while 1:
			Session._create(self, secret)
			try:
				os.lstat("%s/%s" % (self.basedir, self["id"][:2]))
			except OSError, x:
				if x[0] == errno.ENOENT:
					os.mkdir("%s/%s" % (self.basedir, self["id"][:2]), 0700)
			try:
				fd = os.open("%s/%s/%s" % (self.basedir, self["id"][:2], self["id"][2:]), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0700)
			except OSError, x:
				if x[0] != errno.EEXIST:
					raise
				continue
			try:
				os.write(fd, "%d\n" % self.created)
				os.write(fd, pickle.dumps({}, 1))
				break
			finally:
				os.close(fd)

	def _load(self):
		try:
			f = open("%s/%s/%s" % (self.basedir, self["id"][:2], self["id"][2:]), "r+b")
		except IOError, x:
			if x[0] != errno.ENOENT:
				raise
			return 0
		try:
			fcntl.lockf(f.fileno(), fcntl.LOCK_EX)
			self.created = int(f.readline().strip())
			self.update(pickle.load(f))
			return 1
		finally:
			f.close()

	def save(self):
		with open("%s/%s/%s" % (self.basedir, self["id"][:2], self["id"][2:]), "r+b") as f:
			fcntl.lockf(f.fileno(), fcntl.LOCK_EX)
			f.write("%d\n" % self.created)
			pickle.dump(self.copy(), f, 1)
			f.truncate()
			f.flush()
		
	def tidy(cls, max_idle=0, max_age=0, basedir=None):
		if not max_idle and not max_age:
			return
		basedir = cls._find_basedir(basedir)
		now = time.time()
		for d in os.listdir(basedir):
			if len(d) != 2 or not d.isalnum():
				continue
			for f in os.listdir("%s/%s" % (basedir, d)):
				if len(f) != 6 or not f.isalnum():
					continue
				p = "%s/%s/%s" % (basedir, d, f)
				try:
					f = open(p, "rb")
					age = int(f.readline().strip())
				finally:
					f.close()
				if (max_idle and os.lstat(p).st_mtime < now - max_idle) or \
					(max_age and age < now - max_age):
					os.remove(p)
	tidy = classmethod(tidy)

	def _find_basedir(basedir):
		if basedir is None:
			basedir = os.environ.get("TMPDIR", "/tmp")
		while basedir[-1] == "/":
			basedir = basedir[:-1]
		basedir = "%s/sessions-%d" % (basedir, os.getuid())
		try:
			st = os.lstat(basedir)
			if st[4] != os.getuid():
				raise Error("Sessions basedir is not owned by user %d" % os.getuid())
		except OSError, x:
			if x[0] == errno.ENOENT:
				os.mkdir(basedir, 0700)
		return basedir
	_find_basedir = staticmethod(_find_basedir)

	def __init__(self, req, secret, basedir=None, **kwargs):
		self.basedir = self._find_basedir(basedir)
		Session.__init__(self, req, secret, **kwargs)


class GenericSQLSession(Session):
	def _create(self, secret):
		while 1:
			Session._create(self, secret)
			self["hash"] = self._make_hash(self["id"], secret)
			try:
				self.dbc.execute("INSERT INTO %s (ID,hash,created,updated,data)"
					" VALUES (%%s,%%s,%%s,%%s,%%s)" % (self.table,),
					(self["id"], self["hash"], int(self.created), int(self.created),
					pickle.dumps({}, 1)))
				self.dbc.execute("COMMIT")
			except self.dbc.IntegrityError:
				pass
			else:
				break

	def _load(self):
		self.dbc.execute("SELECT created,data FROM %s WHERE ID=%%s" % (self.table,),
			(self["id"],))
		if self.dbc.rowcount == 0:
			return 0
		row = self.dbc.fetchone()
		self.created = row[0]
		self.update(pickle.loads(row[1]))
		return 1

	def save(self):
		self.dbc.execute("UPDATE %s SET updated=%%s,data=%%s"
			" WHERE ID=%%s" % (self.table,), (int(time.time()),
			pickle.dumps(self.copy(), 1), self["id"]))
		self.dbc.execute("COMMIT")

	def tidy(dbc, table="sessions", max_idle=0, max_age=0):
		now = time.time()
		if max_idle:
			dbc.execute("DELETE FROM %s WHERE updated < %%s" % (table,),
				(now - max_idle,))
		if max_age:
			dbc.execute("DELETE FROM %s WHERE created < %%s" % (table,),
				(now - max_age,))
		if max_idle or max_age:
			dbc.execute("COMMIT")
	tidy = staticmethod(tidy)
		
	def __init__(self, req, secret, dbc, table="sessions", **kwargs):
		self.dbc = dbc
		self.table = table
		Session.__init__(self, req, secret, **kwargs)


class MySQLSession(GenericSQLSession):
	def _create(self, secret):
		self.dbc.execute("LOCK TABLES %s WRITE" % (self.table,))
		while 1:
			Session._create(self, secret)
			self.dbc.execute("SELECT 1 FROM %s WHERE ID=%%s" % (self.table,),
				(long(self["id"], 16),))
			if self.dbc.rowcount == 0:
				break
		self["hash"] = self._make_hash(self["id"], secret)
		self.dbc.execute("INSERT INTO %s (ID,hash,created,updated,data) VALUES " \
			"(%%s,%%s,%%s,%%s,%%s)" % (self.table,),
			(long(self["id"], 16), self["hash"], int(self.created),
			int(self.created), pickle.dumps({}, 1)))
		self.dbc.execute("UNLOCK TABLES")

	def _load(self):
		self.dbc.execute("SELECT created,data FROM %s WHERE ID=%%s" % (self.table,),
			(long(self["id"], 16),))
		if self.dbc.rowcount == 0:
			return 0
		row = self.dbc.fetchone()
		self.created = row[0]
		self.update(pickle.loads(row[1]))
		return 1

	def save(self):
		self.dbc.execute("UPDATE %s SET updated=%%s,data=%%s"
			" WHERE ID=%%s" % (self.table,), (int(time.time()),
			pickle.dumps(self.copy(), 1), long(self["id"], 16)))

try:
	import bson
	import pymongo
except ImportError:
	pass
else:
	class MongoDbSession(Session):
		db_name = None
		db_collection = 'sessions'

		def _create(self, secret):
			dt = datetime.datetime.utcnow()
			self.db_connection[self.db_name][self.db_collection].ensure_index('id', unique=True)
			while True:
				Session._create(self, secret)
				self['hash'] = self._make_hash(self['id'], secret)
				try:
					self.db_connection[self.db_name][self.db_collection].insert(bson.son.SON({'id': self['id'], 'hash': self['hash'], 'created': dt, 'updated': dt, 'data': pickle.dumps({})}))
				except pymongo.errors.PyMongoError:
					pass
				else:
					break

		def _load(self):
			obj = self.db_connection[self.db_name][self.db_collection].find_one(bson.son.SON({'id': self['id']}))
			if obj == None:
				return False
			self.created = obj['created']
			self.update(pickle.loads(obj['data'].encode('utf-8')))
			return True

		def save(self):
			dt = datetime.datetime.utcnow()
			self.db_connection[self.db_name][self.db_collection].update(bson.son.SON({'id': self['id']}), bson.son.SON({'$set': {'data': pickle.dumps(self.copy()), 'updated': dt}}))

		@classmethod
		def tidy(self, db_connection, max_idle=0, max_age=0):
			dt = datetime.datetime.utcnow()
			if max_idle:
				db_connection[self.db_name][self.db_collection].remove(bson.son.SON({'updated': {'$lt': dt - max_idle}}))
			if max_age:
				db_connection[self.db_name][self.db_collection].remove(bson.son.SON({'created': {'$lt': dt - max_idle}}))
			
		def __init__(self, req, secret, db_connection, **kwargs):
			self.db_connection = db_connection
			Session.__init__(self, req, secret, **kwargs)


