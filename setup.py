# urlgrabber distutils setup

name = "urlgrabber"
version = "0.3"
description = "high-level cross-protocol url-grabber"
author = "Michael D. Stenner, Ryan Tomayko"
author_email = "mstenner@phy.duke.edu, rtomayko@naeblis.cx"
url = "http://linux.duke.edu/projects/mini/urlgrabber/"
license="GPL"
packages = ['urlgrabber']
package_dir = {'urlgrabber':'urlgrabber'}
scripts = ['scripts/urlgrabber']
data_files = [('share/doc/' + name + '-' + version, ['README','LICENSE', 'TODO', 'ChangeLog'])]
options = { 'clean' : { 'all' : 1 } }

# load up distutils
if __name__ == '__main__':
  config = globals().copy()
  del config['__builtins__']
  del config['__name__']
  
  from distutils.core import setup
  setup(**config)
