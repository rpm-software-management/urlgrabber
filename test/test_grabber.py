#!/usr/bin/python -t

#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License along with this library; if not, write to the 
#      Free Software Foundation, Inc., 
#      59 Temple Place, Suite 330, 
#      Boston, MA  02111-1307  USA

# This file is part of urlgrabber, a high-level cross-protocol url-grabber
# Copyright 2002-2004 Michael D. Stenner, Ryan Tomayko

"""grabber.py tests"""

# $Id: test_grabber.py,v 1.19 2004/08/12 16:08:06 mstenner Exp $

import sys
import os
import string, tempfile, random, cStringIO, os
import urllib2

from base_test_code import *

import urlgrabber
import urlgrabber.grabber as grabber
from urlgrabber.grabber import URLGrabber, URLGrabError
from urlgrabber.progress import text_progress_meter

class FileObjectTests(TestCase):
    
    def setUp(self):
        self.filename = tempfile.mktemp()
        fo = open(self.filename, 'w')
        fo.write(reference_data)
        fo.close()

        self.fo_input = cStringIO.StringIO(reference_data)
        self.fo_output = cStringIO.StringIO()
        self.wrapper = grabber.URLGrabberFileObject('file://' + self.filename, self.fo_output,
                             grabber.default_grabber.opts)

    def tearDown(self):
        os.unlink(self.filename)

    def test_readall(self):
        "URLGrabberFileObject .read() method"
        s = self.wrapper.read()
        self.fo_output.write(s)
        self.assertEqual(reference_data, self.fo_output.getvalue())

    def test_readline(self):
        "URLGrabberFileObject .readline() method"
        while 1:
            s = self.wrapper.readline()
            self.fo_output.write(s)
            if not s: break
        self.assertEqual(reference_data, self.fo_output.getvalue())

    def test_readlines(self):
        "URLGrabberFileObject .readlines() method"
        li = self.wrapper.readlines()
        self.fo_output.write(string.join(li, ''))
        self.assertEqual(reference_data, self.fo_output.getvalue())

    def test_smallread(self):
        "URLGrabberFileObject .read(N) with small N"
        while 1:
            s = self.wrapper.read(23)
            self.fo_output.write(s)
            if not s: break
        self.assertEqual(reference_data, self.fo_output.getvalue())
    
class HTTPTests(TestCase):
    def test_reference_file(self):
        "download refernce file via HTTP"
        filename = tempfile.mktemp()
        grabber.urlgrab(ref_http, filename)

        fo = open(filename)
        contents = fo.read()
        fo.close()

        self.assertEqual(contents, reference_data)

class URLGrabberModuleTestCase(TestCase):
    """Test module level functions defined in grabber.py"""
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
    
    def test_urlopen(self):
        "module-level urlopen() function"
        fo = urlgrabber.urlopen('http://www.python.org')
        fo.close()
    
    def test_urlgrab(self):
        "module-level urlgrab() function"
        outfile = tempfile.mktemp()
        filename = urlgrabber.urlgrab('http://www.python.org', 
                                    filename=outfile)
        os.unlink(outfile)
    
    def test_urlread(self):
        "module-level urlread() function"
        s = urlgrabber.urlread('http://www.python.org')

       
class URLGrabberTestCase(TestCase):
    """Test grabber.URLGrabber class"""
    
    def setUp(self):
        self.meter = text_progress_meter( fo=open('/dev/null', 'w') )
        pass
    
    def tearDown(self):
        pass
    
    def testKeywordArgs(self):
        """grabber.URLGrabber.__init__() **kwargs handling.
        
        This is a simple test that just passes some arbitrary
        values into the URLGrabber constructor and checks that
        they've been set properly.
        """
        opener = urllib2.OpenerDirector()
        g = URLGrabber( progress_obj=self.meter,
                        throttle=0.9,
                        bandwidth=20,
                        retry=20,
                        retrycodes=[5,6,7],
                        copy_local=1,
                        close_connection=1,
                        user_agent='test ua/1.0',
                        proxies={'http' : 'http://www.proxy.com:9090'},
                        opener=opener )
        opts = g.opts
        self.assertEquals( opts.progress_obj, self.meter )
        self.assertEquals( opts.throttle, 0.9 )
        self.assertEquals( opts.bandwidth, 20 )
        self.assertEquals( opts.retry, 20 )
        self.assertEquals( opts.retrycodes, [5,6,7] )
        self.assertEquals( opts.copy_local, 1 )
        self.assertEquals( opts.close_connection, 1 )
        self.assertEquals( opts.user_agent, 'test ua/1.0' )
        self.assertEquals( opts.proxies, {'http' : 'http://www.proxy.com:9090'} )
        self.assertEquals( opts.opener, opener )
        
        nopts = grabber.URLGrabberOptions(delegate=opts, throttle=0.5, 
                                        copy_local=0)
        self.assertEquals( nopts.progress_obj, self.meter )
        self.assertEquals( nopts.throttle, 0.5 )
        self.assertEquals( nopts.bandwidth, 20 )
        self.assertEquals( nopts.retry, 20 )
        self.assertEquals( nopts.retrycodes, [5,6,7] )
        self.assertEquals( nopts.copy_local, 0 )
        self.assertEquals( nopts.close_connection, 1 )
        self.assertEquals( nopts.user_agent, 'test ua/1.0' )
        self.assertEquals( nopts.proxies, {'http' : 'http://www.proxy.com:9090'} )
        nopts.opener = None
        self.assertEquals( nopts.opener, None )
        
    def test_parse_url(self):
        """grabber.URLGrabber._parse_url()"""
        g = URLGrabber()
        (url, parts) = g._parse_url('http://user:pass@host.com/path/part/basename.ext?arg1=val1&arg2=val2#hash')
        (scheme, host, path, parm, query, frag) = parts
        self.assertEquals('http://host.com/path/part/basename.ext?arg1=val1&arg2=val2#hash',url)
        self.assertEquals('http', scheme)
        self.assertEquals('host.com', host)
        self.assertEquals('/path/part/basename.ext', path)
        self.assertEquals('arg1=val1&arg2=val2', query)
        self.assertEquals('hash', frag)
        
    def test_parse_url_local_filename(self):
        """grabber.URLGrabber._parse_url('/local/file/path') """
        g = URLGrabber()
        (url, parts) = g._parse_url('/etc/redhat-release')
        (scheme, host, path, parm, query, frag) = parts
        self.assertEquals('file:///etc/redhat-release',url)
        self.assertEquals('file', scheme)
        self.assertEquals('', host)
        self.assertEquals('/etc/redhat-release', path)
        self.assertEquals('', query)
        self.assertEquals('', frag)

    def test_parse_url_with_prefix(self):
        """grabber.URLGrabber._parse_url() with .prefix"""
        base = 'http://foo.com/dir'
        bases = [base, base+'/']
        file = 'bar/baz'
        target = base + '/' + file
        
        for b in bases:
            g = URLGrabber(prefix=b)
            (url, parts) = g._parse_url(file)
            self.assertEquals(url, target)

    def test_make_callback(self):
        """grabber.URLGrabber._make_callback() tests"""
        def cb(e): pass
        tup_cb = (cb, ('stuff'), {'some': 'dict'})
        g = URLGrabber()
        self.assertEquals(g._make_callback(cb),     (cb, (), {}))
        self.assertEquals(g._make_callback(tup_cb), tup_cb)

class FailureTestCase(TestCase):
    """Test grabber.URLGrabber class"""

    def _failure_callback(self, e):
        self.failure_callback_called = 1
    
    def test_failure_callback_called(self):
        "failure callback is called on retry"
        self.failure_callback_called = 0
        g = grabber.URLGrabber(retry=2,failure_callback=self._failure_callback)
        try: g.urlgrab(ref_404)
        except URLGrabError: pass
        self.assertEquals(self.failure_callback_called, 1)

class RegetTestBase:
    def setUp(self):
        self.ref = short_reference_data
        self.grabber = grabber.URLGrabber(reget='check_timestamp')
        self.filename = tempfile.mktemp()
        self.hl = len(self.ref) / 2
        self.url = 'OVERRIDE THIS'

    def tearDown(self):
        try: os.unlink(self.filename)
        except: pass

    def _make_half_zero_file(self):
        fo = open(self.filename, 'w')
        fo.write('0'*self.hl)
        fo.close()

    def _read_file(self):
        fo = open(self.filename, 'r')
        data = fo.read()
        fo.close()
        return data
    
class CommonRegetTests(RegetTestBase, TestCase):
    def test_bad_reget_type(self):
        "exception raised for illegal reget mode"
        self.assertRaises(URLGrabError, self.grabber.urlgrab,
                          self.url, self.filename, reget='junk')

class FTPRegetTests(RegetTestBase, TestCase):
    def setUp(self):
        RegetTestBase.setUp(self)
        self.url = short_ref_ftp
        # this tests to see if the server is available.  If it's not,
        # then these tests will be skipped
        try:
            fo = urllib2.urlopen(self.url).close()
        except IOError:
            self.skip()

    def test_basic_reget(self):
        'simple (forced) reget'
        self._make_half_zero_file()
        self.grabber.urlgrab(self.url, self.filename, reget='simple')
        data = self._read_file()

        self.assertEquals(data[:self.hl], '0'*self.hl)
        self.assertEquals(data[self.hl:], self.ref[self.hl:])

class HTTPRegetTests(FTPRegetTests):
    def setUp(self):
        RegetTestBase.setUp(self)
        self.url = short_ref_http

    def test_older_check_timestamp(self):
        # define this here rather than in the FTP tests because currently,
        # we get no timestamp information back from ftp servers.
        self._make_half_zero_file()
        ts = 1600000000 # set local timestamp to 2020
        os.utime(self.filename, (ts, ts)) 
        self.grabber.urlgrab(self.url, self.filename, reget='check_timestamp')
        data = self._read_file()

        self.assertEquals(data[:self.hl], '0'*self.hl)
        self.assertEquals(data[self.hl:], self.ref[self.hl:])

    def test_newer_check_timestamp(self):
        # define this here rather than in the FTP tests because currently,
        # we get no timestamp information back from ftp servers.
        self._make_half_zero_file()
        ts = 1 # set local timestamp to 1969
        os.utime(self.filename, (ts, ts)) 
        self.grabber.urlgrab(self.url, self.filename, reget='check_timestamp')
        data = self._read_file()

        self.assertEquals(data, self.ref)

class FileRegetTests(HTTPRegetTests):
    def setUp(self):
        self.ref = short_reference_data
        tmp = tempfile.mktemp()
        tmpfo = open(tmp, 'w')
        tmpfo.write(self.ref)
        tmpfo.close()
        self.tmp = tmp
        
        self.url = 'file://' + tmp

        self.grabber = grabber.URLGrabber(reget='check_timestamp',
                                          copy_local=1)
        self.filename = tempfile.mktemp()
        self.hl = len(self.ref) / 2

    def tearDown(self):
        try: os.unlink(self.filename)
        except: pass
        try: os.unlink(self.tmp)
        except: pass

# I'd like to write some ftp tests as well, but I don't have a
# reliable ftp server

def suite():
    tl = TestLoader()
    return tl.loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    grabber.DEBUG = 0
    runner = TextTestRunner(stream=sys.stdout,descriptions=1,verbosity=2)
    runner.run(suite())
     
