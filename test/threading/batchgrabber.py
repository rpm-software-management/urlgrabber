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

# Copyright 2002-2003 Ryan Tomayko

"""Module for testing urlgrabber under multiple threads.

This module can be used from the command line. Each argument is 
a URL to grab.

The BatchURLGrabber class has an interface similar to URLGrabber 
but instead of pulling files when urlgrab is called, the request
is queued. Calling BatchURLGrabber.batchgrab causes all files to
be pulled in multiple threads.

"""

import os.path, sys
if __name__ == '__main__':
  print os.path.dirname(sys.argv[0])
  sys.path.insert(0, (os.path.dirname(sys.argv[0]) or '.') + '/../..')

from threading import Thread, Semaphore
from urlgrabber.grabber import URLGrabber, URLGrabError
from time import sleep, time
from urlgrabber.progress import text_progress_meter

DEBUG=0

class BatchURLGrabber:
  def __init__(self, maxthreads=5, **kwargs):
    self.maxthreads = 5
    self.grabber = URLGrabber(**kwargs)
    self.queue = []
    self.threads = []
    self.sem = Semaphore()
    
  def urlgrab(self, url, filename=None, **kwargs):
    self.queue.append( (url, filename, kwargs) )
  
  def batchgrab(self):
    while self.queue or self.threads:
      if self.queue and (len(self.threads) < self.maxthreads):
        url, filename, kwargs = self.queue[0]
        del self.queue[0]
        thread = Worker(self, url, filename, kwargs)
        self.threads.append(thread)
        if DEBUG: print "starting worker: " + url
        thread.start()
      else:
        for t in self.threads:
          if not t.isAlive():
            if DEBUG: print "cleaning up worker: " + t.url
            self.threads.remove(t)
        #if len(self.threads) == self.maxthreads:
        #  sleep(0.2)
        sleep(0.2)
        
class Worker(Thread):
  def __init__(self, parent, url, filename, kwargs):
    Thread.__init__(self)
    self.parent = parent
    self.url = url
    self.filename = filename
    self.kwargs = kwargs
  
  def run(self):
    if DEBUG: print "worker thread started."
    grabber = self.parent.grabber
    progress_obj = grabber.opts.progress_obj
    if isinstance(progress_obj, BatchProgressMeter):
      self.kwargs['progress_obj'] = progress_obj.newMeter()
    try:
      rslt = self.parent.grabber.urlgrab(self.url, self.filename, **self.kwargs)
    except URLGrabError, e:
      print '%s, %s' % (e, self.url)

class BatchProgressMeter:
  "An experimental text progress meter that works with multiple threads."
  
  def __init__(self, fo=sys.stdout):
    self.fo = fo
    self.update_period = 0.3 # seconds
    self.meters = []
    self.last_update = 0
    
  def newMeter(self):
    "Create a new meter attached to this guy."
    meter = Meter(self)
    return meter
  
  def meter_start(self, meter):
    "Called when an individual meter starts."
    self.meters.append(meter)
    pass
    
  def meter_end(self, meter):
    "Called when an individual meter ends."
    self.meters.remove(meter)
    self.draw()
    if len(self.meters) == 0:
      self.fo.write('\n')
      self.fo.flush()
    
  def meter_update(self, meter):
    "Called when an individual meter is updated."
    now = time()
    if (now >= self.last_update + self.update_period) or \
          not self.last_update:
      self.last_update = now
      self.draw()
    
  def draw(self):
    out = '\r'
    for meter in self.meters:
      if meter.length:
        try: frac = float(meter.read)/meter.length
        except ZeroDivisionError, e: frac = 1.0
        if frac > 1.0: frac = 1.0
        out+= '[%7.7s:%3i%%]' % (meter.basename, frac*100)
      else:
        out+= '[%7.7s:%5sB]' % (meter.basename, meter.fread)
    # erase previous output
    self.fo.write('\r')
    self.fo.write(' ' * 80)
    self.fo.flush()
    self.fo.write(out[:80] + '\r')
    self.fo.flush()
    
class Meter(text_progress_meter):
  def __init__(self, master):
    self.master = master
    text_progress_meter.__init__(self, fo=None)
    
  def _do_start(self):
    self.master.meter_start(self)
      
  def _do_end(self):
    self.ftotal_time = self.format_time(self.now - self.start_time)
    self.ftotal_size = self.format_number(self.read)
    self.master.meter_end(self)
      
  def _do_update(self, read):
    # elapsed time since last update
    self.read = read
    self.etime = self.now - self.start_time
    self.fetime = self.format_time(self.etime)
    self.fread = self.format_number(read)
    self.master.meter_update(self)
      
def main():
  progress_obj = None
  # uncomment to play with BatchProgressMeter
  #progress_obj=BatchProgressMeter()
  g = BatchURLGrabber(keepalive=1, progress_obj=progress_obj)
  for arg in sys.argv[1:]:
    g.urlgrab(arg)
  if DEBUG: print "before batchgrab"
  try:
    g.batchgrab()
  except KeyboardInterrupt:
    sys.exit(1)
    
  if DEBUG: print "after batchgrab"
  
if __name__ == '__main__':
  main()
