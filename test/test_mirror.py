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

"""mirror.py tests"""

import sys
import os
import tempfile, random, os

import urlgrabber.grabber
from urlgrabber.grabber import URLGrabber, URLGrabError, URLGrabberOptions
import urlgrabber.mirror
from urlgrabber.mirror import MirrorGroup, MGRandomStart, MGRandomOrder

from base_test_code import *

class FakeLogger:
    def __init__(self):
        self.logs = []
    def debug(self, msg, *args):
        self.logs.append(msg % args)
    warn = warning = info = error = debug

class BasicTests(TestCase):
    def setUp(self):
        self.g  = URLGrabber()
        fullmirrors = [base_mirror_url + m + '/' for m in good_mirrors]
        self.mg = MirrorGroup(self.g, fullmirrors)

    def test_urlgrab(self):
        """MirrorGroup.urlgrab"""
        filename = tempfile.mktemp()
        url = 'short_reference'
        self.mg.urlgrab(url, filename)

        data = open(filename, 'rb').read()

        self.assertEqual(data, short_reference_data)

    def test_urlread(self):
        """MirrorGroup.urlread"""
        url = 'short_reference'
        data = self.mg.urlread(url)

        self.assertEqual(data, short_reference_data)

    def test_urlopen(self):
        """MirrorGroup.urlopen"""
        url = 'short_reference'
        fo = self.mg.urlopen(url)
        data = fo.read()
        fo.close()

        self.assertEqual(data, short_reference_data)

class SubclassTests(TestCase):
    def setUp(self):
        self.g  = URLGrabber()
        self.fullmirrors = [base_mirror_url + m + '/' for m in good_mirrors]

    def fetchwith(self, mgclass):
        self.mg = mgclass(self.g, self.fullmirrors)

        filename = tempfile.mktemp()
        url = 'short_reference'
        self.mg.urlgrab(url, filename)

        data = open(filename, 'rb').read()

        self.assertEqual(data, short_reference_data)

    def test_MGRandomStart(self):
        "MGRandomStart.urlgrab"
        self.fetchwith(MGRandomStart)

    def test_MGRandomOrder(self):
        "MGRandomOrder.urlgrab"
        self.fetchwith(MGRandomOrder)

class CallbackTests(TestCase):
    def setUp(self):
        self.g  = URLGrabber()
        fullmirrors = [base_mirror_url + m + '/' for m in \
                       (bad_mirrors + good_mirrors)]
        if hasattr(urlgrabber.grabber, '_TH'):
            # test assumes mirrors are not re-ordered
            urlgrabber.grabber._TH.hosts.clear()
        self.mg = MirrorGroup(self.g, fullmirrors)

    def test_failure_callback(self):
        "test that MG executes the failure callback correctly"
        tricky_list = []
        def failure_callback(cb_obj, tl):
            tl.append(str(cb_obj.exception))
        self.mg.failure_callback = failure_callback, (tricky_list, ), {}
        data = self.mg.urlread('reference')
        self.assertTrue(data == reference_data)
        self.assertEqual(tricky_list[0][:25],
                          '[Errno 14] HTTP Error 404')

    def test_callback_reraise(self):
        "test that the callback can correctly re-raise the exception"
        def failure_callback(cb_obj): raise cb_obj.exception
        self.mg.failure_callback = failure_callback
        self.assertRaises(URLGrabError, self.mg.urlread, 'reference')

class BadMirrorTests(TestCase):
    def setUp(self):
        self.g  = URLGrabber()
        fullmirrors = [base_mirror_url + m + '/' for m in bad_mirrors]
        self.mg = MirrorGroup(self.g, fullmirrors)

    def test_simple_grab(self):
        """test that a bad mirror raises URLGrabError"""
        filename = tempfile.mktemp()
        url = 'reference'
        self.assertRaises(URLGrabError, self.mg.urlgrab, url, filename)

class FailoverTests(TestCase):
    def setUp(self):
        self.g  = URLGrabber()
        fullmirrors = [base_mirror_url + m + '/' for m in \
                       (bad_mirrors + good_mirrors)]
        self.mg = MirrorGroup(self.g, fullmirrors)

    def test_simple_grab(self):
        """test that a the MG fails over past a bad mirror"""
        filename = tempfile.mktemp()
        url = 'reference'
        elist = []
        def cb(e, elist=elist): elist.append(e)
        self.mg.urlgrab(url, filename, failure_callback=cb)

        contents = open(filename, 'rb').read()

        # first be sure that the first mirror failed and that the
        # callback was called
        self.assertEqual(len(elist), 1)
        # now be sure that the second mirror succeeded and the correct
        # data was returned
        self.assertEqual(contents, reference_data)

class FakeGrabber:
    def __init__(self, resultlist=None):
        self.resultlist = resultlist or []
        self.index = 0
        self.calls = []
        self.opts = URLGrabberOptions()

    def urlgrab(self, url, filename=None, **kwargs):
        self.calls.append( (url, filename) )
        res = self.resultlist[self.index]
        self.index += 1
        if isinstance(res, Exception): raise res
        else: return res

class ActionTests(TestCase):
    def setUp(self):
        self.snarfed_logs = []
        self.db = urlgrabber.mirror.DEBUG
        urlgrabber.mirror.DEBUG = FakeLogger()
        self.mirrors = ['a', 'b', 'c', 'd', 'e', 'f']
        self.g = FakeGrabber([URLGrabError(3), URLGrabError(3), 'filename'])
        self.mg = MirrorGroup(self.g, self.mirrors)

    def tearDown(self):
        urlgrabber.mirror.DEBUG = self.db

    def test_defaults(self):
        'test default action policy'
        self.mg.urlgrab('somefile')
        expected_calls = [ (m.encode('utf8') + b'/somefile', None)
                           for m in self.mirrors[:3] ]
        expected_logs = \
            ['MIRROR: trying somefile -> a/somefile',
             'MIRROR: failed',
             'GR   mirrors: [b c d e f] 0',
             'MAIN mirrors: [a b c d e f] 1',
             'MIRROR: trying somefile -> b/somefile',
             'MIRROR: failed',
             'GR   mirrors: [c d e f] 0',
             'MAIN mirrors: [a b c d e f] 2',
             'MIRROR: trying somefile -> c/somefile']

        self.assertEqual(self.g.calls, expected_calls)
        self.assertEqual(urlgrabber.mirror.DEBUG.logs, expected_logs)

    def test_instance_action(self):
        'test the effects of passed-in default_action'
        self.mg.default_action = {'remove_master': 1}
        self.mg.urlgrab('somefile')
        expected_calls = [ (m.encode('utf8') + b'/somefile', None)
                           for m in self.mirrors[:3] ]
        expected_logs = \
            ['MIRROR: trying somefile -> a/somefile',
             'MIRROR: failed',
             'GR   mirrors: [b c d e f] 0',
             'MAIN mirrors: [b c d e f] 0',
             'MIRROR: trying somefile -> b/somefile',
             'MIRROR: failed',
             'GR   mirrors: [c d e f] 0',
             'MAIN mirrors: [c d e f] 0',
             'MIRROR: trying somefile -> c/somefile']

        self.assertEqual(self.g.calls, expected_calls)
        self.assertEqual(urlgrabber.mirror.DEBUG.logs, expected_logs)

    def test_method_action(self):
        'test the effects of method-level default_action'
        self.mg.urlgrab('somefile', default_action={'remove_master': 1})
        expected_calls = [ (m.encode('utf8') + b'/somefile', None)
                           for m in self.mirrors[:3] ]
        expected_logs = \
            ['MIRROR: trying somefile -> a/somefile',
             'MIRROR: failed',
             'GR   mirrors: [b c d e f] 0',
             'MAIN mirrors: [b c d e f] 0',
             'MIRROR: trying somefile -> b/somefile',
             'MIRROR: failed',
             'GR   mirrors: [c d e f] 0',
             'MAIN mirrors: [c d e f] 0',
             'MIRROR: trying somefile -> c/somefile']

        self.assertEqual(self.g.calls, expected_calls)
        self.assertEqual(urlgrabber.mirror.DEBUG.logs, expected_logs)


    def callback(self, e): return {'fail': 1}

    def test_callback_action(self):
        'test the effects of a callback-returned action'
        self.assertRaises(URLGrabError, self.mg.urlgrab, 'somefile',
                          failure_callback=self.callback)
        expected_calls = [ (m.encode('utf8') + b'/somefile', None)
                           for m in self.mirrors[:1] ]
        expected_logs = \
                      ['MIRROR: trying somefile -> a/somefile',
                       'MIRROR: failed',
                       'GR   mirrors: [b c d e f] 0',
                       'MAIN mirrors: [a b c d e f] 1']

        self.assertEqual(self.g.calls, expected_calls)
        self.assertEqual(urlgrabber.mirror.DEBUG.logs, expected_logs)

import threading, socket

class HttpReplyCode(TestCase):
    def setUp(self):
        # start the server
        self.exit = False
        self.process = lambda data: None

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', 0)); s.listen(1)
        self.port = s.getsockname()[1]

        def server():
            while True:
                c, a = s.accept()
                if self.exit: c.close(); break
                data = b''
                while not data.endswith(b'\r\n\r\n'):
                    data = c.recv(4096)
                self.process(data)
                c.sendall(b'HTTP/1.1 %d %s\r\n' % self.reply)
                if self.content is not None:
                    c.sendall(b'Content-Length: %d\r\n\r\n' % len(self.content))
                    c.sendall(self.content)
                c.close()
            s.close()
            self.exit = False

        self.thread = threading.Thread(target=server)
        self.thread.start()

        # create grabber and mirror group objects
        def failure(obj):
            self.code = getattr(obj.exception, 'code', None)
            return {}
        self.g  = URLGrabber()
        self.mg = MirrorGroup(self.g, ['http://localhost:%d' % self.port],
                              failure_callback = failure)

    def tearDown(self):
        # shut down the server
        self.exit = True
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(('localhost', self.port)) # wake it up
        except ConnectionRefusedError:
            # already gone?
            pass
        s.close()
        self.thread.join()

    def test_grab(self):
        'tests the propagation of HTTP reply code'
        self.reply = 503, b'Busy'
        self.content = None

        # single
        self.assertRaises(URLGrabError, self.mg.urlgrab, 'foo')
        self.assertEqual(self.code, 503); del self.code

        # multi
        err = []
        self.mg.urlgrab('foo', async_=True, failfunc=err.append)
        urlgrabber.grabber.parallel_wait()
        self.assertEqual([e.exception.errno for e in err], [256])
        self.assertEqual(self.code, 503); del self.code

    def test_range(self):
        'test client-side processing of HTTP ranges'
        # server does not process ranges
        self.reply = 200, b'OK'
        self.content = b'ABCDEF'

        # no range specified
        data = self.mg.urlread('foo')
        self.assertEqual(data, b'ABCDEF')

        data = self.mg.urlread('foo', range = (3, 5))
        self.assertEqual(data, b'DE')

    def test_retry_no_cache(self):
        'test bypassing proxy cache on failure'
        def process(data):
            if b'Pragma:no-cache' in data:
                self.content = b'version2'
            else:
                self.content = b'version1'

        def checkfunc_read(obj):
            if obj.data == 'version1':
                raise URLGrabError(-1, 'Outdated version of foo')

        def checkfunc_grab(obj):
            with open('foo') as f:
                if f.read() == 'version1':
                    raise URLGrabError(-1, 'Outdated version of foo')

        self.process = process
        self.reply = 200, b'OK'

        opts = self.g.opts
        opts.retry = 3
        opts.retry_no_cache = True

        # single
        opts.checkfunc = checkfunc_read
        try:
            self.mg.urlread('foo')
        except URLGrabError as e:
            self.fail(str(e))

        # multi
        opts.checkfunc = checkfunc_grab
        self.mg.urlgrab('foo', async_=True)
        try:
            urlgrabber.grabber.parallel_wait()
        except URLGrabError as e:
            self.fail(str(e))

def suite():
    tl = TestLoader()
    return tl.loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    runner = TextTestRunner(stream=sys.stdout,descriptions=1,verbosity=2)
    runner.run(suite())
