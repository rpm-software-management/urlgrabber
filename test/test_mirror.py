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

# Copyright 2002-2004 Michael D. Stenner, Ryan D. Tomayko

import sys
import os
import unittest
import string, tempfile, random, cStringIO, os

import urlgrabber.grabber
from urlgrabber.grabber import URLGrabber, URLGrabError
import urlgrabber.mirror
from urlgrabber.mirror import MirrorGroup

from base_test_code import *

def suite():
    classlist = [BasicTests, BadMirrorTests, FailoverTests, CallbackTests]
    return unittest.TestSuite(makeSuites(classlist))

class BasicTests(UGTestCase):
    def setUp(self):
        self.g  = URLGrabber()
        fullmirrors = [base_mirror_url + m + '/' for m in good_mirrors]
        self.mg = MirrorGroup(self.g, fullmirrors)

    def test_simple_grab(self):
        """test that a reference file can be properly downloaded"""
        filename = tempfile.mktemp()
        url = 'reference'
        self.mg.urlgrab(url, filename)

        fo = open(filename)
        contents = fo.read()
        fo.close()

        self.assertEqual(contents, reference_data)

class CallbackTests(UGTestCase):
    def setUp(self):
        self.g  = URLGrabber()
        fullmirrors = [base_mirror_url + m + '/' for m in \
                       (bad_mirrors + good_mirrors)]
        self.mg = MirrorGroup(self.g, fullmirrors)
    
    def test_failure_callback(self):
        "test that MG executes the failure callback correctly"
        tricky_list = []
        def failure_callback(e, tl): tl.append(str(e))
        self.mg.failure_callback = failure_callback, (tricky_list, ), {}
        data = self.mg.urlread('reference')
        self.assert_(data == reference_data)
        self.assertEquals(tricky_list,
                          ['[Errno 4] IOError: HTTP Error 403: Forbidden'])

class BadMirrorTests(UGTestCase):
    def setUp(self):
        self.g  = URLGrabber()
        fullmirrors = [base_mirror_url + m + '/' for m in bad_mirrors]
        self.mg = MirrorGroup(self.g, fullmirrors)

    def test_simple_grab(self):
        """test that a bad mirror raises URLGrabError"""
        filename = tempfile.mktemp()
        url = 'reference'
        self.assertRaises(URLGrabError, self.mg.urlgrab, url, filename)

class FailoverTests(UGTestCase):
    def setUp(self):
        self.g  = URLGrabber()
        fullmirrors = [base_mirror_url + m + '/' for m in \
                       (bad_mirrors + good_mirrors)]
        self.mg = MirrorGroup(self.g, fullmirrors)

    def test_simple_grab(self):
        """test that a the MG fails over past a bad mirror"""
        filename = tempfile.mktemp()
        url = 'reference'
        self.mg.urlgrab(url, filename)

        fo = open(filename)
        contents = fo.read()
        fo.close()

        self.assertEqual(contents, reference_data)

if __name__ == '__main__':
    urlgrabber.grabber.DEBUG = 0
    urlgrabber.mirror.DEBUG = 0
    runner = unittest.TextTestRunner(descriptions=1,verbosity=2)
    runner.run(suite())
     
