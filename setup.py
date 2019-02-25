# urlgrabber distutils setup
import re as _re
import sys as _sys

class _pycurlFake(object):
    Curl = staticmethod(lambda: None)

# Unforunately __init__.py imports urlgrabber.grabber which then imports
# pycurl package. And finally pycurl.Curl() is called in the top level
# of grabber module. We don't need pycurl nor pycurl.Curl() during
# setup. Fake this module to be loaded already so we don't need to have
# pycurl installed at all. Maybe developer wants to install it in later
# phase.
_sys.modules["pycurl"] = _pycurlFake

# We need urlgrabber package for some constants.
import urlgrabber as _urlgrabber

del _sys.modules["pycurl"]

name = "urlgrabber"
description = "A high-level cross-protocol url-grabber"
long_description = _urlgrabber.__doc__
license = "LGPLv2+"
version = _urlgrabber.__version__
_authors = _re.split(r',\s+', _urlgrabber.__author__)
author       = ', '.join([_re.sub(r'\s+<.*',        r'', _) for _ in _authors])
author_email = ', '.join([_re.sub(r'(^.*<)|(>.*$)', r'', _) for _ in _authors])
url = _urlgrabber.__url__

packages = ['urlgrabber']
package_dir = {'urlgrabber':'urlgrabber'}
scripts = ['scripts/urlgrabber']
data_files = [
    ('share/doc/' + name + '-' + version, ['README','LICENSE', 'TODO', 'ChangeLog']),
    ('libexec', ['scripts/urlgrabber-ext-down']),
]
setup_requires = ['six']
install_requires = ['pycurl', 'six']
options = { 'clean' : { 'all' : 1 } }
classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Internet :: File Transfer Protocol (FTP)',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules'
      ]

# load up distutils
if __name__ == '__main__':
  config = globals().copy()
  keys = list(config.keys())
  for k in keys:
    #print '%-20s -> %s' % (k, config[k])
    if k.startswith('_'): del config[k]

  from setuptools import setup
  setup(**config)
