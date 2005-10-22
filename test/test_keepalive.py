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

"""keepalive.py tests"""

# $Id: test_keepalive.py,v 1.11 2005/10/22 21:57:27 mstenner Exp $

import sys
import os
import time
import urllib2
import threading
import re

from urllib2 import URLError, HTTPError

from base_test_code import *

from urlgrabber import keepalive

class FakeLogger:
    def __init__(self):
        self.logs = []
    def debug(self, msg, *args):
        self.logs.append(msg % args)
    warn = warning = info = error = debug

class CorruptionTests(TestCase):
    def setUp(self):
        self.kh = keepalive.HTTPHandler()
        self.opener = urllib2.build_opener(self.kh)
        self.ref = ref_http
        self.fo = self.opener.open(self.ref)
        
    def tearDown(self):
        self.fo.close()
        self.kh.close_all()
        
    def test_readall(self):
        "download a file with a single call to read()"
        data = self.fo.read()
        self.assert_(data == reference_data)

    def test_readline(self):
        "download a file with multiple calls to readline()"
        data = ''
        while 1:
            s = self.fo.readline()
            if s: data = data + s
            else: break
        self.assert_(data == reference_data)

    def test_readlines(self):
        "download a file with a single call to readlines()"
        lines = self.fo.readlines()
        data = ''.join(lines)
        self.assert_(data == reference_data)

    def test_smallread(self):
        "download a file with multiple calls to read(23)"
        data = ''
        while 1:
            s = self.fo.read(23)
            if s: data = data + s
            else: break
        self.assert_(data == reference_data)

    def test_mixed_read(self):
        "download a file with mixed readline() and read(23) calls"
        data = ''
        while 1:
            s = self.fo.read(23)
            if s: data = data + s
            else: break
            s = self.fo.readline()
            if s: data = data + s
            else: break
        self.assert_(data == reference_data)

class HTTPErrorTests(TestCase):
    def setUp(self):
        self.kh = keepalive.HTTPHandler()
        self.opener = urllib2.build_opener(self.kh)
        import sys
        self.python_version = sys.version_info
        
    def tearDown(self):
        self.kh.close_all()
        keepalive.HANDLE_ERRORS = 1

    def test_200_handler_on(self):
        "test that 200 works with fancy handler"
        keepalive.HANDLE_ERRORS = 1
        fo = self.opener.open(ref_http)
        data = fo.read()
        fo.close()
        self.assertEqual((fo.status, fo.reason), (200, 'OK'))

    def test_200_handler_off(self):
        "test that 200 works without fancy handler"
        keepalive.HANDLE_ERRORS = 0
        fo = self.opener.open(ref_http)
        data = fo.read()
        fo.close()
        self.assertEqual((fo.status, fo.reason), (200, 'OK'))

    def test_404_handler_on(self):
        "test that 404 works with fancy handler"
        keepalive.HANDLE_ERRORS = 1
        self.assertRaises(URLError, self.opener.open, ref_404)

    def test_404_handler_off(self):
        "test that 404 works without fancy handler"
        keepalive.HANDLE_ERRORS = 0
        ## see the HANDLE_ERRORS note in keepalive.py for discussion of
        ## the changes in python 2.4
        if self.python_version >= (2, 4):
            self.assertRaises(URLError, self.opener.open, ref_404)
        else:
            fo = self.opener.open(ref_404)
            data = fo.read()
            fo.close()
            self.assertEqual((fo.status, fo.reason), (404, 'Not Found'))

    def test_403_handler_on(self):
        "test that 403 works with fancy handler"
        keepalive.HANDLE_ERRORS = 1
        self.assertRaises(URLError, self.opener.open, ref_403)

    def test_403_handler_off(self):
        "test that 403 works without fancy handler"
        keepalive.HANDLE_ERRORS = 0
        ## see the HANDLE_ERRORS note in keepalive.py for discussion of
        ## the changes in python 2.4
        if self.python_version >= (2, 4):
            self.assertRaises(URLError, self.opener.open, ref_403)
        else:
            fo = self.opener.open(ref_403)
            data = fo.read()
            fo.close()
            self.assertEqual((fo.status, fo.reason), (403, 'Forbidden'))

class DroppedConnectionTests(TestCase):
    def setUp(self):
        self.kh = keepalive.HTTPHandler()
        self.opener = urllib2.build_opener(self.kh)
        self.db = keepalive.DEBUG
        keepalive.DEBUG = FakeLogger()
        
    def tearDown(self):
        self.kh.close_all()
        keepalive.DEBUG = self.db
        
    def test_dropped_connection(self):
        "testing connection restarting (20-second delay, ctrl-c to skip)"
        # the server has a 15-second keepalive timeout (the apache default)
        fo = self.opener.open(ref_http)
        data1 = fo.read()
        fo.close()

        try: time.sleep(20)
        except KeyboardInterrupt: self.skip()
        
        fo = self.opener.open(ref_http)
        data2 = fo.read()
        fo.close()
        
        reference_logs = [
            'creating new connection to www.linux.duke.edu',
            'STATUS: 200, OK',
            'failed to re-use connection to www.linux.duke.edu',
            'creating new connection to www.linux.duke.edu',
            'STATUS: 200, OK'
            ]
        self.assert_(data1 == data2)
        l = [ re.sub(r'\s+\(-?\d+\)$', r'', line) for \
              line in keepalive.DEBUG.logs ]
        self.assert_(l == reference_logs)
        
class ThreadingTests(TestCase):
    def setUp(self):
        self.kh = keepalive.HTTPHandler()
        self.opener = urllib2.build_opener(self.kh)
        self.snarfed_logs = []
        self.db = keepalive.DEBUG
        keepalive.DEBUG = FakeLogger()

    def tearDown(self):
        self.kh.close_all()
        keepalive.DEBUG = self.db

    def test_basic_threading(self):
        "use 3 threads, each getting a file 4 times"
        numthreads = 3
        cond = threading.Condition()
        self.threads = []
        for i in range(numthreads):
            t = Fetcher(self.opener, ref_http, 4)
            t.start()
            self.threads.append(t)
        for t in self.threads: t.join()
        l = [ re.sub(r'\s+\(-?\d+\)$', r'', line) for \
              line in keepalive.DEBUG.logs ]
        l.sort()
        creating = ['creating new connection to www.linux.duke.edu'] * 3
        status = ['STATUS: 200, OK'] * 12
        reuse = ['re-using connection to www.linux.duke.edu'] * 9
        reference_logs = creating + status + reuse
        reference_logs.sort()
        if 0:
            print '--------------------'
            for log in l: print log
            print '--------------------'
            for log in reference_logs: print log
            print '--------------------'
        self.assert_(l == reference_logs)
            
class Fetcher(threading.Thread):
    def __init__(self, opener, url, num):
        threading.Thread.__init__(self)
        self.opener = opener
        self.url = url
        self.num = num
        
    def run(self):
        for i in range(self.num):
            fo = self.opener.open(self.url)
            data = fo.read()
            fo.close()
    
def suite():
    tl = TestLoader()
    return tl.loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    runner = TextTestRunner(stream=sys.stdout,descriptions=1,verbosity=2)
    runner.run(suite())
     
