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

# Copyright 2002-2003 Michael D. Stenner, Ryan Tomayko

import sys
import os
from os.path import dirname, join as joinpath

if __name__ == '__main__':
    dn = dirname(sys.argv[0])
    sys.path.insert(0, joinpath(dn,'..'))
    sys.path.insert(0, dn)

import tempfile
import time

import grabber
from grabber import URLGrabber, urlgrab, urlopen, urlread
from progress import text_progress_meter

tempsrc = '/tmp/ug-test-src'
tempdst = '/tmp/ug-test-dst'

DEBUG=0

def main():
    speedtest(1024)         # 1KB
    speedtest(10 * 1024)    # 10 KB
    speedtest(100 * 1024)   # 100 KB
    speedtest(1000 * 1024)  # 1,000 KB (almost 1MB)
    speedtest(10000 * 1024) # 10,000 KB (almost 10MB)
    # remove temp files
    os.unlink(tempsrc)
    os.unlink(tempdst)
    
def setuptemp(size):
    if DEBUG: print 'writing %d KB to temporary file (%s).' % (size / 1024, tempsrc)
    file = open(tempsrc, 'w', 1024)
    chars = '0123456789'
    for i in range(size):
        file.write(chars[i % 10])
    file.flush()
    file.close()
    
def speedtest(size):
    setuptemp(size)
    full_times = []
    raw_times = []
    throttle = 2**40 # throttle to 1 TB/s   :)

    try:
        from progress import text_progress_meter
    except ImportError, e:
        tpm = None
        print 'not using progress meter'
    else:
        tpm = text_progress_meter(fo=open('/dev/null', 'w'))
        
    # to address concerns that the overhead from the progress meter
    # and throttling slow things down, we do this little test.
    #
    # using this test, you get the FULL overhead of the progress
    # meter and throttling, without the benefit: the meter is directed
    # to /dev/null and the throttle bandwidth is set EXTREMELY high.
    #
    # note: it _is_ even slower to direct the progress meter to a real
    # tty or file, but I'm just interested in the overhead from _this_
    # module.
    
    # get it nicely cached before we start comparing
    if DEBUG: print 'pre-caching'
    for i in range(100):
        urlgrab(tempsrc, tempdst, copy_local=1, throttle=None)
    
    if DEBUG: print 'running speed test.'
    reps = 500
    for i in range(reps):
        if DEBUG: 
            print '\r%4i/%-4i' % (i+1, reps),
            sys.stdout.flush()
        t = time.time()
        urlgrab(tempsrc, tempdst,
                copy_local=1, progress_obj=tpm,
                throttle=throttle)
        full_times.append(1000 * (time.time() - t))

        t = time.time()
        urlgrab(tempsrc, tempdst,
                copy_local=1, progress_obj=None,
                throttle=None)
        raw_times.append(1000 * (time.time() - t))
    if DEBUG: print '\r'
    
    print "%d KB Results:" % (size / 1024)
    full_times.sort()
    full_mean = 0.0
    for i in full_times: full_mean = full_mean + i
    full_mean = full_mean/len(full_times)
    print '[full] mean: %.3f ms, median: %.3f ms, min: %.3f ms, max: %.3f ms' % \
          (full_mean, full_times[int(len(full_times)/2)], min(full_times),
           max(full_times))

    raw_times.sort()
    raw_mean = 0.0
    for i in raw_times: raw_mean = raw_mean + i
    raw_mean = raw_mean/len(raw_times)
    print '[raw]  mean: %.3f ms, median: %.3f ms, min: %.3f ms, max: %.3f ms' % \
          (raw_mean, raw_times[int(len(raw_times)/2)], min(raw_times),
           max(raw_times))

    grabber.close_all()

if __name__ == '__main__':
    main()
