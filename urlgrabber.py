# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# Copyright 2002-2003 Michael D. Stenner

import os
import os.path
import urlparse
import rfc822
import time
import string

DEBUG=0
VERSION='0.2'

try:
    from i18n import _
except ImportError, msg:
    def _(st): return st

try:
    from httplib import HTTPException
except ImportError, msg:
    HTTPException = None

special_handlers = []

try:
    import urllib2
except ImportError, msg:
    import urllib
    urllib._urlopener = urllib.FancyURLopener() # make sure it ready now
    urllib2 = urllib   # this way, we can always just do urllib.urlopen()
    have_urllib2 = 0
    auth_handler = None
else:
    have_urllib2 = 1
    auth_handler = urllib2.HTTPBasicAuthHandler( \
        urllib2.HTTPPasswordMgrWithDefaultRealm())
    special_handlers.append(auth_handler)

try:
    # This is a convenient way to make keepalive optional.
    # Just rename the module so it can't be imported.
    from keepalive import HTTPHandler
except ImportError, msg:
    keepalive_handler = None
else:
    keepalive_handler = HTTPHandler()
    special_handlers.append(keepalive_handler)

if have_urllib2:
    opener = apply(urllib2.build_opener, special_handlers)
    urllib2.install_opener(opener)

def set_user_agent(new_user_agent):
    if have_urllib2: addheaders = opener.addheaders
    else:            addheaders = urllib._urlopener.addheaders

    new_tuple = ('User-agent', new_user_agent)

    for i in range(len(addheaders)):
        if addheaders[i][0] == 'User-agent':
            addheaders[i] = new_tuple
            break
    else:
        addheaders.append(new_tuple)

# the calling application can override this user-agent by calling
# urlgrabber.set_user_agent
set_user_agent('urlgrabber/%s' % VERSION)

class URLGrabError(IOError):
    """
    URLGrabError error codes:
      -1 - default retry code for retrygrab check functions
      0  - everything looks good (you should never see this)
      1  - malformed url
      2  - local file doesn't exist
      3  - request for non-file local file (dir, etc)
      4  - IOError on fetch
      5  - OSError on fetch
      6  - no content length header when we expected one
      7  - HTTPException
      8  - Exceeded read limit (for urlread)
 
    Negative codes are reserved for use by functions passed in to
    retrygrab with checkfunc.

    You can use it like this:
      try: urlgrab(url)
      except URLGrabError, e:
         if e.errno == 3: ...
           # or
         print e.strerror
           # or simply
         print e  #### print '[Errno %i] %s' % (e.errno, e.strerror)
    """
    pass

def close_all():
    """close any open keepalive connections"""
    if keepalive_handler: keepalive_handler.close_all()

_throttle = 1.0
_bandwidth = 0
def set_throttle(new_throttle):
    """urlgrab supports throttling via two values: throttle and bandwidth
    Between the two, you can either specify and absolute throttle threshold
    or specify a theshold as a fraction of maximum available bandwidth.
    
    throttle is a number - if it's an int, it's the bytes/second throttle
       limit.  If it's a float, it is first multiplied by bandwidth.  If
       throttle == 0, throttling is disabled.  If None, the module-level
       default (which can be set with set_throttle) is used.

    bandwidth is the nominal max bandwidth in bytes/second.  If throttle
       is a float and bandwidth == 0, throttling is disabled.  If None,
       the module-level default (which can be set with set_bandwidth) is
       used.

    EXAMPLES:

      Lets say you have a 100 Mbps connection.  This is (about) 10^8 bits
      per second, or 12,500,000 Bytes per second.  You have a number of
      throttling options:

      *) set_bandwidth(12500000); set_throttle(0.5) # throttle is a float

         This will limit urlgrab to use half of your available bandwidth.

      *) set_throttle(6250000) # throttle is an int

         This will also limit urlgrab to use half of your available
         bandwidth, regardless of what bandwidth is set to.

      *) set_throttle(6250000); set_throttle(1.0) # float

         Use half your bandwidth

      *) set_throttle(6250000); set_throttle(2.0) # float

         Use up to 12,500,000 Bytes per second (your nominal max bandwidth)

      *) set_throttle(6250000); set_throttle(0) # throttle = 0

         Disable throttling - this is more efficient than a very large
         throttle setting.

      *) set_throttle(0); set_throttle(1.0) # throttle is float, bandwidth = 0

         Disable throttling - this is the default when the module is loaded.


    SUGGESTED AUTHOR IMPLEMENTATION

      While this is flexible, it's not extremely obvious to the user.  I
      suggest you implement a float throttle as a percent to make the
      distinction between absolute and relative throttling very explicit.

      Also, you may want to convert the units to something more convenient
      than bytes/second, such as kbps or kB/s, etc.
    """
    global _throttle
    _throttle = new_throttle

def set_bandwidth(new_bandwidth):
    global _bandwidth
    _bandwidth = new_bandwidth

_progress_obj = None
def set_progress_obj(new_progress_obj):
    global _progress_obj
    _progress_obj = new_progress_obj


def retrygrab(url, filename=None, copy_local=0, close_connection=0,
              progress_obj=None, throttle=None, bandwidth=None,
              numtries=3, retrycodes=[-1,2,4,5,6,7], checkfunc=None):
    """a wrapper function for urlgrab that retries downloads

    The args for retrygrab are the same as urlgrab except for numtries,
    retrycodes, and checkfunc.  You should use keyword arguments for
    both in case new args are added to urlgrab later.  If you use keyword
    args (especially for the retrygrab-specific options) then retrygrab
    will continue to be a drop-in replacement for urlgrab.  Otherwise,
    things may break.

    retrygrab exits just like urlgrab in either case.  Either it
    returns the local filename or it raises an exception.  The
    exception raised will be the one raised MOST RECENTLY by urlgrab.

    retrygrab ONLY retries if URLGrabError is raised.  If urlgrab (or
    checkfunc) raise some other exception, it will be passed up
    immediately.

    numtries
       number of times to retry the grab before bailing.  If this is
       zero, it will retry forever.  This was intentional... really,
       it was :)

    retrycodes
       the errorcodes (values of e.errno) for which it should retry.
       See the doc on URLGrabError for more details on this.

    checkfunc
       a function to do additional checks.  This defaults to None,
       which means no additional checking.  The function should simply
       return on a successful check.  It should raise URLGrabError on
       and unsuccessful check.  Raising of any other exception will
       be considered immediate failure and no retries will occur.

       Negative error numbers are reserved for use by these passed in
       functions.  By default, -1 results in a retry, but this can be
       customized with retrycodes.

       If you simply pass in a function, it will be given exactly one
       argument: the local file name as returned by urlgrab.  If you
       need to pass in other arguments,  you can do so like this:

         checkfunc=(function, ('arg1', 2), {'kwarg': 3})

       if the downloaded file as filename /tmp/stuff, then this will
       result in this call:

         function('/tmp/stuff', 'arg1', 2, kwarg=3)

       NOTE: both the "args" tuple and "kwargs" dict must be present
       if you use this syntax, but either (or both) can be empty.
    """

    tries = 0
    if not checkfunc is None:
        if callable(checkfunc):
            func, args, kwargs = checkfunc, (), {}
        else:
            func, args, kwargs = checkfunc
    else:
        func = None

    while 1:
        tries = tries + 1
        if DEBUG: print 'TRY #%i: %s' % (tries, url)
        try:
            fname = urlgrab(url, filename, copy_local, close_connection,
                            progress_obj, throttle, bandwidth)
            if not func is None: apply(func, (fname, )+args, kwargs)
            if DEBUG: print 'RESULT = success (%s)' % fname
            return fname
        except URLGrabError, e:
            if DEBUG: print 'EXCEPTION: %s' % e
            if tries == numtries or (e.errno not in retrycodes): raise

def urlgrab(url, filename=None, copy_local=0, close_connection=0,
            progress_obj=None, throttle=None, bandwidth=None):
    """grab the file at <url> and make a local copy at <filename>

    If filename is none, the basename of the url is used.

    copy_local is ignored except for file:// urls, in which case it
    specifies whether urlgrab should still make a copy of the file, or
    simply point to the existing copy.

    close_connection tells urlgrab to close the connection after
    completion.  This is ignored unless the download happens with the
    http keepalive handler.  Otherwise, the connection is left open
    for further use.

    progress_obj is a class instance that supports the following methods:
       po.start(filename, url, basename, length)
       # length will be None if unknown
       po.update(read) # read == bytes read so far
       po.end()

    throttle is a number - if it's an int, it's the bytes/second throttle
       limit.  If it's a float, it is first multiplied by bandwidth.  If
       throttle == 0, throttling is disabled.  If None, the module-level
       default (which can be set with set_throttle) is used.

    bandwidth is the nominal max bandwidth in bytes/second.  If throttle
       is a float and bandwidth == 0, throttling is disabled.  If None,
       the module-level default (which can be set with set_bandwidth) is
       used.

    urlgrab returns the filename of the local file, which may be different
    from the passed-in filename if copy_local == 0.
    """

    url, parts = _parse_url(url)
    (scheme, host, path, parm, query, frag) = parts

    if filename == None:
        filename = os.path.basename(path)
    if scheme == 'file' and not copy_local:
        # just return the name of the local file - don't make a copy
        # currently we don't do anything with the progress_cb here
        if not os.path.exists(path):
            raise URLGrabError(2, _('Local file does not exist: %s') % (path, ))
        elif not os.path.isfile(path):
            raise URLGrabError(3, _('Not a normal file: %s') % (path, ))
        else:
            return path

    raw_throttle = _get_raw_throttle(throttle, bandwidth)
    if progress_obj is None: progress_obj = _progress_obj
    elif not progress_obj: progress_obj = None
    fo, hdr = _do_open(url)

    # download and store the file
    try:
        if progress_obj or raw_throttle:
            if progress_obj:
                try:    length = int(hdr['Content-Length'])
                except: length = None
                progress_obj.start(filename, url, os.path.basename(path), length)
            fo = URLGrabberFileObject(fo, progress_obj, raw_throttle)
        _do_grab(filename, fo, hdr)
        fo.close()

        if close_connection:
            # try and close connection
            try: fo.close_connection()
            except AttributeError: pass
    except IOError, e:
        raise URLGrabError(4, _('IOError: %s') % (e, ))
    except OSError, e:
        raise URLGrabError(5, _('OSError: %s') % (e, ))
    except HTTPException, e:
        raise URLGrabError(7, _('HTTP Error (%s): %s') % \
                           (e.__class__.__name__, e))

    return filename

def urlopen(url, progress_obj=None, throttle=None, bandwidth=None):
    """open the url and return a file object

    If a progress object or throttle specifications exist, then
    a special file object will be returned that supports them.
    The file object can be treated like any other file object.
    """
    url, parts = _parse_url(url)
    (scheme, host, path, parm, query, frag) = parts
    raw_throttle = _get_raw_throttle(throttle, bandwidth)
    if progress_obj is None: progress_obj = _progress_obj
    fo, hdr = _do_open(url)
    if progress_obj or raw_throttle:
        if progress_obj:
            try:    length = int(hdr['Content-Length'])
            except: length = None
            progress_obj.start(None, url, os.path.basename(path), length)
        fo = URLGrabberFileObject(fo, progress_obj, raw_throttle)
    return fo

def urlread(url, progress_obj=None, throttle=None, bandwidth=None, limit=None):
    """read the url into a string, up to 'limit' bytes

    If the limit is exceeded, an exception will be thrown.  Note that urlread
    is NOT intended to be used as a way of saying "I want the first N bytes"
    but rather 'read the whole file into memory, but don't use too much'
    """
    fo = urlopen(url, progress_obj, throttle, bandwidth)
    s = fo.read(limit+1)
    fo.close()
    if limit and len(s) > limit:
        raise URLGrabError(8, _('Exceeded limit (%i): %s') % (limit, url))
    return s

class URLGrabberFileObject:
    """This is a file-object wrapper that supports progress objects and
    throttling.

    This exists to solve the following problem: lets say you want to
    drop-in replace a normal open with urlopen.  You want to use a
    progress meter and/or throttling, but how do you do that without
    rewriting your code?  Answer: urlopen will return a wrapped file
    object that does the progress meter and-or throttling internally.
    """

    def __init__(self, fo, progress_obj, raw_throttle):
        self.fo = fo
        self.raw_throttle = raw_throttle
        self.progress_obj = progress_obj
        self._rbuf = ''
        self._rbufsize = 1024*8
        self._ttime = time.time()
        self._tsize = 0
        self._amount_read = 0
        if progress_obj: progress_obj.update(0)
        
    def __getattr__(self, name):
        """This effectively allows us to wrap at the instance level.
        Any attribute not found in _this_ object will be searched for
        in self.fo.  This includes methods."""
        if hasattr(self.fo, name):
            return getattr(self.fo, name)
        raise AttributeError, name

    def _fill_buffer(self, amt=None):
        """fill the buffer to contain at least 'amt' bytes by reading
        from the underlying file object.  If amt is None, then it will
        read until it gets nothing more.  It updates the progress meter
        and throttles after every self._rbufsize bytes."""
        # the _rbuf test is only in this first 'if' for speed.  It's not
        # logically necessary
        if self._rbuf and not amt is None:
            L = len(self._rbuf)
            if amt > L:
                amt = amt - L
            else:
                return

        # if we've made it here, then we don't have enough in the buffer
        # and we need to read more.

        buf = [self._rbuf]
        bufsize = len(self._rbuf)
        while amt is None or amt:
            # first, delay if necessary for throttling reasons
            if self.raw_throttle:
                diff = self._tsize/self.raw_throttle - \
                       (time.time() - self._ttime)
                if diff > 0: time.sleep(diff)
                self._ttime = time.time()
                
            # now read some data, up to self._rbufsize
            if amt is None: readamount = self._rbufsize
            else:           readamount = min(amt, self._rbufsize)
            new = self.fo.read(readamount)
            newsize = len(new)
            if not newsize: break # no more to read

            if amt: amt = amt - newsize
            buf.append(new)
            bufsize = bufsize + newsize
            self._tsize = newsize
            self._amount_read = self._amount_read + newsize
            if self.progress_obj:
                self.progress_obj.update(self._amount_read)

        self._rbuf = string.join(buf, '')
        return

    def read(self, amt=None):
        self._fill_buffer(amt)
        if amt is None:
            s, self._rbuf = self._rbuf, ''
        else:
            s, self._rbuf = self._rbuf[:amt], self._rbuf[amt:]
        return s

    def readline(self, limit=-1):
        i = string.find(self._rbuf, '\n')
        while i < 0 and not (0 < limit <= len(self._rbuf)):
            L = len(self._rbuf)
            self._fill_buffer(L + self._rbufsize)
            if not len(self._rbuf) > L: break
            i = string.find(self._rbuf, '\n', L)

        if i < 0: i = len(self._rbuf)
        else: i = i+1
        if 0 <= limit < len(self._rbuf): i = limit

        s, self._rbuf = self._rbuf[:i], self._rbuf[i:]
        return s

    def close(self):
        if self.progress_obj:
            self.progress_obj.end()
        self.fo.close()
        
def _parse_url(url):
    """break up the url into its component parts

    This function disassembles a url and
    1) "normalizes" it, tidying it up a bit
    2) does any authentication stuff it needs to do

    it returns the (cleaned) url and a tuple of component parts
    """
    (scheme, host, path, parm, query, frag) = urlparse.urlparse(url)
    path = os.path.normpath(path)
    if '@' in host and auth_handler and scheme in ['http', 'https']:
        try:
            # should we be using urllib.splituser and splitpasswd instead?
            user_password, host = string.split(host, '@', 1)
            user, password = string.split(user_password, ':', 1)
        except ValueError, e:
            raise URLGrabError(1, _('Bad URL: %s') % url)
        if DEBUG: print 'adding HTTP auth: %s, %s' % (user, password)
        auth_handler.add_password(None, host, user, password)

    parts = (scheme, host, path, parm, query, frag)
    return urlparse.urlunparse(parts), parts

def _get_raw_throttle(throttle, bandwidth):
    if throttle == None: throttle = _throttle
    if throttle <= 0: raw_throttle = 0
    elif type(throttle) == type(0): raw_throttle = float(throttle)
    else: # throttle is a float
        if bandwidth == None: bandwidth = _bandwidth
        raw_throttle = bandwidth * throttle
    return raw_throttle

def _do_open(url):
    """initiate the connection & get the headers
    return the file object and header object
    """
    try:
        fo = urllib2.urlopen(url)
        hdr = fo.info()
    except ValueError, e:
        raise URLGrabError(1, _('Bad URL: %s') % (e, ))
    except IOError, e:
        raise URLGrabError(4, _('IOError: %s') % (e, ))
    except OSError, e:
        raise URLGrabError(5, _('OSError: %s') % (e, ))
    except HTTPException, e:
        raise URLGrabError(7, _('HTTP Error (%s): %s') % \
                           (e.__class__.__name__, e))

    # OK, this "cute little hack" may have outlived its usefulness.
    # the role of urlgrabber is expaning and we're wanting it to handle
    # things (like cgi output) that this is preventing.  For now, I'm
    # simply going to comment it out and see what breaks.

    # this is a cute little hack - if there isn't a "Content-Length"
    # header then its probably something generated dynamically, such
    # as php, cgi, a directory listing, or an error message.  It is
    # probably not what we want.
    #if have_urllib2 or scheme != 'file':
    #    # urllib does not provide content-length for local files
    #    if not hdr is None and not hdr.has_key('Content-Length'):
    #        raise URLGrabError(6, _('ERROR: Url Return no Content-Length  - something is wrong'))

    return fo, hdr

_last_modified_format = '%a, %d %b %Y %H:%M:%S %Z'
def _do_grab(filename, fo, hdr):
    """dump the file to filename"""
    new_fo = open(filename, 'wb')
    bs = 1024*8
    size = 0

    block = fo.read(bs)
    size = size + len(block)
    while block:
        new_fo.write(block)
        block = fo.read(bs)
        size = size + len(block)
        
    new_fo.close()

    try:
        modified_tuple  = hdr.getdate_tz('last-modified')
        modified_stamp  = rfc822.mktime_tz(modified_tuple)
        os.utime(filename, (modified_stamp, modified_stamp))
    except (TypeError,), e: pass

    return size

#####################################################################
#  TESTING
def _main_test():
    import sys
    try: url, filename = sys.argv[1:3]
    except ValueError:
        print 'usage:', sys.argv[0], \
              '<url> <filename> [copy_local=0|1] [close_connection=0|1]'
        sys.exit()

    kwargs = {}
    for a in sys.argv[3:]:
        k, v = string.split(a, '=', 1)
        kwargs[k] = int(v)

    set_throttle(1.0)
    set_bandwidth(32 * 1024)
    print "throttle: %s,  throttle bandwidth: %s B/s" % (_throttle, _bandwidth)

    try: from progress_meter import text_progress_meter
    except ImportError, e: pass
    else: kwargs['progress_obj'] = text_progress_meter()

    try: name = apply(urlgrab, (url, filename), kwargs)
    except URLGrabError, e: print e
    else: print 'LOCAL FILE:', name


def _speed_test():
    #### speed test --- see comment below
    import sys
    
    full_times = []
    raw_times = []
    set_throttle(2**40) # throttle to 1 TB/s   :)

    try:
        from progress_meter import text_progress_meter
    except ImportError, e:
        tpm = None
        print 'not using progress meter'
    else:
        tpm = text_progress_meter(fo=open('/dev/null', 'w'))

    # to address concerns that the overhead from the progress meter
    # and throttling slow things down, we do this little test.  Make
    # sure /tmp/test holds a sanely-sized file (like .2 MB)
    #
    # using this test, you get the FULL overhead of the progress
    # meter and throttling, without the benefit: the meter is directed
    # to /dev/null and the throttle bandwidth is set EXTREMELY high.
    #
    # note: it _is_ even slower to direct the progress meter to a real
    # tty or file, but I'm just interested in the overhead from _this_
    # module.
    
    # get it nicely cached before we start comparing
    print 'pre-caching'
    for i in range(100):
        urlgrab('file:///tmp/test', '/tmp/test2',
                copy_local=1)

    reps = 1000
    for i in range(reps):
        print '\r%4i/%-4i' % (i, reps),
        sys.stdout.flush()
        t = time.time()
        urlgrab('file:///tmp/test', '/tmp/test2',
                copy_local=1, progress_obj=tpm)
        full_times.append(1000 * (time.time() - t))

        t = time.time()
        urlgrab('file:///tmp/test', '/tmp/test2',
                copy_local=1, progress_obj=None)
        raw_times.append(1000* (time.time() - t))
    print '\r'
    
    full_times.sort()
    full_mean = 0.0
    for i in full_times: full_mean = full_mean + i
    full_mean = full_mean/len(full_times)
    print '[full] mean: %.3f ms, median: %.3f ms, min: %.3f ms, max: %.3f ms' % \
          (full_mean, full_times[int(len(full_times)/2)], min(full_times),
           max(full_times))

    raw_times.sort()
    raw_mean = 0.0
    for i in raw_times: raw_mean = raw_mean + i
    raw_mean = raw_mean/len(raw_times)
    print '[raw]  mean: %.3f ms, median: %.3f ms, min: %.3f ms, max: %.3f ms' % \
          (raw_mean, raw_times[int(len(raw_times)/2)], min(raw_times),
           max(raw_times))

    close_all()

def _retry_test():
    import sys
    try: url, filename = sys.argv[1:3]
    except ValueError:
        print 'usage:', sys.argv[0], \
              '<url> <filename> [copy_local=0|1] [close_connection=0|1]'
        sys.exit()

    kwargs = {}
    for a in sys.argv[3:]:
        k, v = string.split(a, '=', 1)
        kwargs[k] = int(v)

    try: from progress_meter import text_progress_meter
    except ImportError, e: pass
    else: kwargs['progress_obj'] = text_progress_meter()

    global DEBUG
    #DEBUG = 1
    def cfunc(filename, hello, there='foo'):
        print hello, there
        import random
        rnum = random.random()
        if rnum < .5:
            print 'forcing retry'
            raise URLGrabError(-1, 'forcing retry')
        if rnum < .75:
            print 'forcing failure'
            raise URLGrabError(-2, 'forcing immediate failure')
        print 'success'
        return
        
    close_all()
    kwargs['checkfunc'] = (cfunc, ('hello',), {'there':'there'})
    try: name = apply(retrygrab, (url, filename), kwargs)
    except URLGrabError, e: print e
    else: print 'LOCAL FILE:', name

if __name__ == '__main__':
    _main_test()
    #_speed_test()
    #_retry_test()
    #_file_object_test()
    
