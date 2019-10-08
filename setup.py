from setuptools import setup

pkg_name = "urlgrabber"
pkg_version = "4.1.0"

setup(
    name=pkg_name,
    version=pkg_version,
    license="LGPLv2+",
    description="A high-level cross-protocol url-grabber",
    keywords="urlgrabber yum http ftp",
    # From https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # Development status
        "Development Status :: 5 - Production/Stable",
        # Target audience
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        # Type of software
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        # Kind of software
        "Environment :: Console",
        "Environment :: Web Environment",
        # License (must match license field)
        "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
        # Operating systems supported
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        # Supported Python versions
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    url="http://urlgrabber.baseurl.org/",
    author="Michael D. Stenner, Ryan Tomayko, Seth Vidal, Zdenek Pavlas",
    author_email="mstenner@linux.duke.edu, rtomayko@naeblis.cx, skvidal@fedoraproject.org, zpavlas@redhat.com",
    maintainer="Neal Gompa",
    maintainer_email="ngompa@fedoraproject.org",
    packages=["urlgrabber"],
    package_dir = {'urlgrabber':'urlgrabber'},
    include_package_data=True,
    install_requires=[
        "pycurl",
        "six",
        "setuptools",
    ],
    scripts = ['scripts/urlgrabber'],
    data_files = [
        ('share/doc/' + pkg_name + '-' + pkg_version, ['README','LICENSE', 'TODO', 'ChangeLog']),
        ('libexec', ['scripts/urlgrabber-ext-down']),
   ],
)
