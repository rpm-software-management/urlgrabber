#!/usr/bin/python -t
#
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

# Copyright 2002-2003 Michael D. Stenner, Ryan D. Tomayko

import sys
import unittest
import os
import string, tempfile, random, cStringIO, os
from unittest import TestCase, TestSuite

from base_test_code import *

import urlgrabber
import urlgrabber.grabber as grabber
from urlgrabber.grabber import URLGrabber, URLGrabError
from urlgrabber.progress import text_progress_meter

def suite():
    classlist = [FileObjectTests, HTTPTests, URLGrabberModuleTestCase,
                 URLGrabberTestCase, RegetTests]
    s = UGSuite(makeSuites(classlist))
    s.description = "grabber.py tests"
    return s

class FileObjectTests(UGTestCase):
    
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
    
class HTTPTests(UGTestCase):
    def test_reference_file(self):
        "download refernce file via HTTP"
        filename = tempfile.mktemp()
        grabber.urlgrab(ref_http, filename)

        fo = open(filename)
        contents = fo.read()
        fo.close()

        self.assertEqual(contents, reference_data)

class URLGrabberModuleTestCase(UGTestCase):
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
        "module-level urlgrab() function"
        s = urlgrabber.urlread('http://www.python.org')

       
class URLGrabberTestCase(UGTestCase):
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
        g = URLGrabber( progress_obj=self.meter,
                        throttle=0.9,
                        bandwidth=20,
                        retry=20,
                        retrycodes=[5,6,7],
                        copy_local=1,
                        close_connection=1,
                        user_agent='test ua/1.0',
                        proxies={'http' : 'http://www.proxy.com:9090'} )
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

class RegetTests(UGTestCase):
    def setUp(self):
        self.ref = short_reference_data
        self.grabber = grabber.URLGrabber(reget='check_timestamp')
        self.filename = tempfile.mktemp()
        self.hl = len(self.ref) / 2

    def tearDown(self):
        try: os.unlink(self.filename)
        except: pass

    def test_bad_reget_type(self):
        "exception raised for illegal reget mode"
        self.assertRaises(URLGrabError, self.grabber.urlgrab,
                          short_ref_http, self.filename, reget='junk')

    def _make_half_zero_file(self):
        fo = open(self.filename, 'w')
        fo.write('0'*self.hl)
        fo.close()

    def _read_file(self):
        fo = open(self.filename, 'r')
        data = fo.read()
        fo.close()
        return data
    
    def test_basic_reget(self):
        'simple (forced) reget'
        self._make_half_zero_file()
        self.grabber.urlgrab(short_ref_http, self.filename, reget='simple')
        data = self._read_file()

        self.assertEquals(data[:self.hl], '0'*self.hl)
        self.assertEquals(data[self.hl:], self.ref[self.hl:])

    def test_older_check_timestamp(self):
        'reget when server version is older than local'
        self._make_half_zero_file()
        ts = 1600000000 # set local timestamp to 2020
        os.utime(self.filename, (ts, ts)) 
        self.grabber.urlgrab(short_ref_http,
                             self.filename, reget='check_timestamp')
        data = self._read_file()

        self.assertEquals(data[:self.hl], '0'*self.hl)
        self.assertEquals(data[self.hl:], self.ref[self.hl:])

    def test_newer_check_timestamp(self):
        'NO reget when server version is newer than local'
        self._make_half_zero_file()
        ts = 1 # set local timestamp to 1969
        os.utime(self.filename, (ts, ts)) 
        self.grabber.urlgrab(short_ref_http,
                             self.filename, reget='check_timestamp')
        data = self._read_file()

        self.assertEquals(data, self.ref)

# I'd like to write some ftp tests as well, but I don't have a
# reliable ftp server

if __name__ == '__main__':
    grabber.DEBUG = 0
    runner = unittest.TextTestRunner(descriptions=1,verbosity=2)
    runner.run(suite())
     
