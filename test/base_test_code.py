import unittest
from unittest import TestResult

base_http = 'http://www.linux.duke.edu/projects/urlgrabber/test/'

reference_data = ''.join( [str(i)+'\n' for i in range(20000) ] )
ref_http = base_http + 'reference'
short_reference_data = ' '.join( [str(i) for i in range(10) ] )
short_ref_http = base_http + 'short_reference'

ref_200 = ref_http
ref_404 = base_http + 'nonexistent_file'
ref_403 = base_http + 'mirror/broken/'

base_mirror_url    = base_http + 'mirror/'
good_mirrors       = ['m1', 'm2', 'm3']
mirror_files       = ['test1.txt', 'test2.txt']
bad_mirrors        = ['broken']
bad_mirror_files   = ['broken.txt']

class Skip(Exception): pass

class UGSuite(unittest.TestSuite):
    def __call__(self, result):
        try: result.startSuite(self)
        except AttributeError: pass
        
        for test in self._tests:
            if result.shouldStop:
                break
            test(result)

        try: result.endSuite(self)
        except AttributeError: pass

        return result

    def shortDescription(self):
        return getattr(self, 'description', '(no description)')

class UGResult(unittest._TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        unittest._TextTestResult.__init__(self, stream, descriptions,
                                          verbosity)
        self.indent = '  '
        self.depth = 0

    def addSkip(self, test, err):
        if self.showAll:
            self.stream.writeln("skip")
        elif self.dots:
            self.stream.write('s')

    def startTest(self, test):
        TestResult.startTest(self, test)
        if self.showAll:
            self.stream.write(self.indent * self.depth)
            self.stream.write(self.getDescription(test))
            self.stream.write(" ... ")

    def startSuite(self, suite):
        if self.showAll:
            self.stream.write(self.indent * self.depth)
            try: desc = self.getDescription(suite)
            except AttributeError: desc = '(no description)'
            self.stream.writeln(desc)
        self.depth += 1
        
    def endSuite(self, suite):
        self.depth -= 1

class UGRunner(unittest.TextTestRunner):
    def _makeResult(self):
        return UGResult(self.stream, self.descriptions, self.verbosity)

class UGTestCase(unittest.TestCase):
    skipException = Skip
    def shortDescription(self):
        doc = self._TestCase__testMethodDoc
        #doc = self.__testMethodDoc
        doc = doc and (doc.split('\n'))[0].strip()
        doc = doc or self._TestCase__testMethodName
        return '%-63s' % doc

    def defaultTestResult(self):
        return UGResult()

    def __call__(self, result=None):
        if result is None: result = self.defaultTestResult()
        result.startTest(self)
        testMethod = getattr(self, self._TestCase__testMethodName)
        try:
            try:
                self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._TestCase__exc_info())
                return

            ok = 0
            try:
                testMethod()
                ok = 1
            except self.failureException, e:
                result.addFailure(self, self._TestCase__exc_info())
            except self.skipException, e:
                result.addSkip(self, self._TestCase__exc_info())
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._TestCase__exc_info())

            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._TestCase__exc_info())
                ok = 0
            if ok: result.addSuccess(self)
        finally:
            result.stopTest(self)


def makeSuites(classlist, prefix='test'):
    return [ UGmakeSuite(c, prefix) for c in classlist ]

def UGmakeSuite(testCaseClass, prefix='test', sortUsing=cmp,
                suiteClass=UGSuite):
    loader = unittest._makeLoader(prefix, sortUsing, suiteClass)
    s = loader.loadTestsFromTestCase(testCaseClass)
    if hasattr(testCaseClass, 'description'):
        s.description = testCaseClass.description
    else:
        s.description = testCaseClass.__name__
    return s
