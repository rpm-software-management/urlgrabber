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

# Copyright 2002-2006 Michael D. Stenner, Ryan Tomayko
# Copyright 2009 Red Hat, Inc - pycurl support added by Seth Vidal


"""A high-level cross-protocol url-grabber.

Using urlgrabber, data can be fetched in three basic ways:

  urlgrab(url) copy the file to the local filesystem
  urlopen(url) open the remote file and return a file object
     (like urllib2.urlopen)
  urlread(url) return the contents of the file as a string

When using these functions (or methods), urlgrabber supports the
following features:

  * identical behavior for http://, ftp://, and file:// urls
  * http keepalive - faster downloads of many files by using
    only a single connection
  * byte ranges - fetch only a portion of the file
  * reget - for a urlgrab, resume a partial download
  * progress meters - the ability to report download progress
    automatically, even when using urlopen!
  * throttling - restrict bandwidth usage
  * retries - automatically retry a download if it fails. The
    number of retries and failure types are configurable.
  * authenticated server access for http and ftp
  * proxy support - support for authenticated http and ftp proxies
  * mirror groups - treat a list of mirrors as a single source,
    automatically switching mirrors if there is a failure.
"""

try:
    from email import message_from_string
    from pkg_resources import get_distribution
    pkgInfo = get_distribution(__package__).get_metadata('PKG-INFO')
    __metadata__ = message_from_string(pkgInfo)
    del pkgInfo

    __version__ = __metadata__['Version']
    __author__  = __metadata__['Author']
    __url__     = __metadata__['Home-page']
except:
    __author__ = __version__ = __url__ = '<see setup.cfg>'

from .grabber import urlgrab, urlopen, urlread
