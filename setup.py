from distutils.core import setup
setup(name="urlgrabber",
      version="0.3",
      description="high-level cross-protocol url-grabber",
      author="Michael D. Stenner, Ryan Tomayko",
      author_email="mstenner@phy.duke.edu, rtomayko@naeblis.cx",
      url="http://linux.duke.edu/projects/mini/urlgrabber/",
      license="GPL",
      packages=['URLGrabber'],
      package_dir={'URLGrabber' : ''},
      scripts=['scripts/urlgrabber'],
      data_files=[
          ('share/doc', ['README','LICENSE', 'TODO'])
          ],
      options = { 
        'clean' : { 'all' : 1 }
        },
      )
