#!/usr/bin/python
import sys
sys.path.insert(0, '.')

import unittest
import urlgrabber

import string, tempfile, random, cStringIO, os

reference_data = ''.join( [str(i)+'\n' for i in range(20000) ] )


class FileObjectTests(unittest.TestCase):
    def setUp(self):
        self.filename = tempfile.mktemp()
        fo = open(self.filename, 'w')
        fo.write(reference_data)
        fo.close()

        self.fo_input = cStringIO.StringIO(reference_data)
        self.fo_output = cStringIO.StringIO()
        self.wrapper = urlgrabber.URLGrabberFileObject(self.fo_input, None, 0)

    def tearDown(self):
        os.unlink(self.filename)

    def test_readall(self):
        s = self.wrapper.read()
        self.fo_output.write(s)
        self.assertEqual(reference_data, self.fo_output.getvalue())

    def test_readline(self):
        while 1:
            s = self.wrapper.readline()
            self.fo_output.write(s)
            if not s: break
        self.assertEqual(reference_data, self.fo_output.getvalue())

    def test_readlines(self):
        li = self.wrapper.readlines()
        self.fo_output.write(string.join(li, ''))
        self.assertEqual(reference_data, self.fo_output.getvalue())

    def test_smallread(self):
        while 1:
            s = self.wrapper.read(23)
            self.fo_output.write(s)
            if not s: break
        self.assertEqual(reference_data, self.fo_output.getvalue())
    
class HTTPTests(unittest.TestCase):
    base_url = 'http://www.linux.duke.edu/projects/mini/urlgrabber/test/'
    def test_reference_file(self):
        """test that a reference file can be properly downloaded via http"""
        filename = tempfile.mktemp()
        url = self.base_url + 'reference'
        urlgrabber.urlgrab(url, filename)

        fo = open(filename)
        contents = fo.read()
        fo.close()

        self.assertEqual(contents, reference_data)

# I'd like to write some ftp tests as well, but I don't have a
# reliable ftp server

if __name__ == '__main__':
    unittest.main()
