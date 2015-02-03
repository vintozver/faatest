# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys
import os
import re
import stat
import time
import urllib

from util.handler import Handler as _base
from util.handler import HandlerError as _base_error

class HandlerError(_base_error):
	pass

class HandlerBase(_base):
	@classmethod
	def get_ranges(cls, hdr, length):
	    """Return a list of (start, stop) indices from a Range header, or None.
	    
	    Each (start, stop) tuple will be composed of two ints, which are suitable
	    for use in a slicing operation. That is, the header "Range: bytes=3-6",
	    if applied against a Python string, is requesting resource[3:7]. This
	    function will return the list [(3, 7)].
	    
	    If this function returns an empty list, you should return HTTP 416.
	    """
	    
	    if not hdr:
		return None
	    
	    result = []
	    bytesunit, byteranges = hdr.split("=", 1)
	    for brange in byteranges.split(","):
		start, stop = [x.strip() for x in brange.split("-", 1)]
		if start:
		    if not stop:
			stop = length - 1
		    start, stop = map(int, (start, stop))
		    if start >= length:
			# From rfc 2616 sec 14.16:
			# "If the server receives a request (other than one
			# including an If-Range request-header field) with an
			# unsatisfiable Range request-header field (that is,
			# all of whose byte-range-spec values have a first-byte-pos
			# value greater than the current length of the selected
			# resource), it SHOULD return a response code of 416
			# (Requested range not satisfiable)."
			continue
		    if stop < start:
			# From rfc 2616 sec 14.16:
			# "If the server ignores a byte-range-spec because it
			# is syntactically invalid, the server SHOULD treat
			# the request as if the invalid Range header field
			# did not exist. (Normally, this means return a 200
			# response containing the full entity)."
			return None
		    result.append((start, stop + 1))
		else:
		    if not stop:
			# See rfc quote above.
			return None
		    # Negative subscript (last N bytes)
		    result.append((length - int(stop), length))
    
	    return result

	@classmethod
	def file_generator_limited(cls, fileobj, count, chunk_size=65536):
	    """Yield the given file object in chunks, stopping after `count`
	    bytes has been emitted.  Default chunk size is 64kB. (Core)
	    """
	    remaining = count
	    while remaining > 0:
		chunk = fileobj.read(min(chunk_size, remaining))
		chunklen = len(chunk)
		if chunklen == 0:
		    return
		remaining -= chunklen
		yield chunk

	def mimetype(self, path):
		return 'application/octet-stream'

	def __call__(self, path, content_type=None, disposition=None, name=None):
	    """Set status, headers, and body in order to serve the given file.
	    
	    The Content-Type header will be set to the content_type arg, if provided.
	    If not provided, the Content-Type will be guessed by the file extension
	    of the 'path' argument.
	    
	    If disposition is not None, the Content-Disposition header will be set
	    to "<disposition>; filename=<name>". If name is None, it will be set
	    to the basename of path. If disposition is None, no Content-Disposition
	    header will be written.
	    """
	    
	    if self.req.method not in ('GET', 'HEAD'):
		return False
	    
	    # If path is relative, raise an error
	    if not os.path.isabs(path):
		raise HandlerError('Absolute path is required', path)

	    # If path is relative, users should fix it by making path absolute.
	    # That is, CherryPy should not guess where the application root is.
	    # It certainly should *not* use cwd (since CP may be invoked from a
	    # variety of paths). If using tools.static, you can make your relative
	    # paths become absolute by supplying a value for "tools.static.root".
	    if not os.path.isabs(path):
		raise HandlerError('Absolute path is required', path)
	    
	    try:
		st = os.stat(path)
	    except OSError:
		raise HandlerError('Not found', path)
	    
	    # Check if path is a directory.
	    if stat.S_ISDIR(st.st_mode):
		# Let the caller deal with it as they like.
		raise HandlerError('Not found', path)

	    self.req.setResponseCode(200, 'OK')
	    
	    # Set the Last-Modified response header, so that
	    # modified-since validation code can work.
	    lastmod = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(st.st_mtime))
	    self.req.setHeader('Last-Modified', lastmod)
	    if lastmod:
		status = 200
		
		since = self.req.request_headers.get('If-Unmodified-Since')
		if since and since != lastmod:
		    if (status >= 200 and status <= 299) or status == 412:
			self.req.setResponseCode(412, 'Precondition Failed')
			return
		
		since = self.req.request_headers.get('If-Modified-Since')
		if since and since == lastmod:
		    if (status >= 200 and status <= 299) or status == 304:
			if self.req.method in ("GET", "HEAD"):
			    self.req.setResponseCode(304, 'Not Modified')
			    return
			else:
			    self.req.setResponseCode(412, 'Precondition Failed')
			    return
	    
	    if content_type is None:
		content_type = self.mimetype(path)
	    self.req.setHeader('Content-Type', content_type)
	    
	    if disposition is not None:
		if name is None:
		    name = os.path.basename(path)
		cd = '%s; filename="%s"' % (disposition, name)
		self.req.setHeader('Content-Disposition', cd)
	    
	    # Set Content-Length and use an iterable (file object)
	    #   this way CP won't load the whole file in memory
	    c_len = st.st_size
	    bodyfile = open(path, 'rb')
	    
	    # HTTP/1.0 didn't have Range/Accept-Ranges headers, or the 206 code
	    if self.req.clientproto >= 'HTTP/1.0':
		self.req.setHeader('Accept-Ranges', 'bytes')
		r = self.get_ranges(self.req.request_headers.get('Range'), c_len)
		if r == []:
		    self.req.setHeader('Content-Range', 'bytes */%s' % c_len)
		    message = "Invalid Range (first-byte-pos greater than Content-Length)"
		    self.req.setResponseCode(416, 'Invalid Range (first-byte-pos greater than Content-Length)')
		    return
		if r:
		    if len(r) == 1:
			# Return a single-part response.
			start, stop = r[0]
			if stop > c_len:
			    stop = c_len
			r_len = stop - start
			self.req.setResponseCode(206, 'Partial Content')
			self.req.setHeader('Content-Range', 'bytes %s-%s/%s' % (start, stop - 1, c_len))
			self.req.setHeader('Content-Length', r_len)
			bodyfile.seek(start)
			for file_part in self.file_generator_limited(bodyfile, r_len):
				self.req.write(file_part)
		    else:
			# Return a multipart/byteranges response.
			self.req.setResponseCode(206, 'Partial Content')
			import mimetools
			boundary = mimetools.choose_boundary()
			ct = "multipart/byteranges; boundary=%s" % boundary
			self.req.setHeader('Content-Type', ct)
			if self.req.getHeader('Content-Length'):
			    # Delete Content-Length header so finalize() recalcs it.
			    self.req.responseHeaders.removeHeader('Content-Length')
			
			def file_ranges():
			    # Apache compatibility:
			    yield "\r\n"
			    
			    for start, stop in r:
				yield "--" + boundary
				yield "\r\nContent-type: %s" % content_type
				yield ("\r\nContent-range: bytes %s-%s/%s\r\n\r\n"
				       % (start, stop - 1, c_len))
				bodyfile.seek(start)
				for chunk in self.file_generator_limited(bodyfile, stop-start):
				    yield chunk
				yield "\r\n"
			    # Final boundary
			    yield "--" + boundary + "--"
			    
			    # Apache compatibility:
			    yield "\r\n"
			for file_range in file_ranges():
			    self.req.write(file_range)
		else:
		    self.req.setHeader('Content-Length', c_len)
		    self.req.write(bodyfile.read())
	    else:
		self.req.setHeader('Content-Length', c_len)
		self.req.write(bodyfile.read())


class Handler(HandlerBase):
	def mimetype(self, path):
		# Set content-type based on filename extension
		MAP = {
			'.htm': 'text/html',
			'.html': 'text/html',
			'.css': 'text/css',
			'.js': 'text/javascript',
			'.jpg': 'image/jpeg',
			'.jpeg': 'image/jpeg',
			'.gif': 'image/gif',
			'.png': 'image/png',
			'.avi': 'video/avi',
			'.ico': 'image/x-icon',
		}

		ext = ''
		i = path.rfind('.')
		if i != -1:
			ext = path[i:].lower()

		return MAP.get(ext, 'text/plain')

