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

def suite():
    return unittest.TestSuite((
        unittest.makeSuite(BasicTests,'test'),
        unittest.makeSuite(BadMirrorTests,'test'),
        unittest.makeSuite(FailoverTests,'test'),
        ))

reference_data = ''.join( [str(i)+'\n' for i in range(20000) ] )
base_url = 'http://www.linux.duke.edu/projects/mini/urlgrabber/test/mirror/'
mirrors  = ['m1', 'm2', 'm3']
files    = ['test1.txt', 'test2.txt']
bmirrors = ['broken']
bfiles   = ['broken.txt']

class BasicTests(unittest.TestCase):
    def setUp(self):
        self.g  = URLGrabber()
        fullmirrors = [base_url + m + '/' for m in mirrors]
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

class BadMirrorTests(unittest.TestCase):
    def setUp(self):
        self.g  = URLGrabber()
        fullmirrors = [base_url + m + '/' for m in bmirrors]
        self.mg = MirrorGroup(self.g, fullmirrors)

    def test_simple_grab(self):
        """test that a bad mirror raises URLGrabError"""
        filename = tempfile.mktemp()
        url = 'reference'
        self.assertRaises(URLGrabError, self.mg.urlgrab, url, filename)

class FailoverTests(unittest.TestCase):
    def setUp(self):
        self.g  = URLGrabber()
        fullmirrors = [base_url + m + '/' for m in bmirrors + mirrors]
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
     
