RM = /bin/rm -f
WEBHOST = login.dulug.duke.edu
WEBPATH = /home/groups/urlgrabber/web/download
PYTHON = python

ChangeLog: FORCE
	maint/cvs2cl.pl -S -U maint/usermap --utc --no-times

dist: ChangeLog
	$(PYTHON) setup.py sdist --force-manifest
	scp dist/* $(WEBHOST):$(WEBPATH)/

clean:
	$(RM) MANIFEST
	$(RM) -r dist/
	$(RM) *.pyc urlgrabber/*.pyc scripts/*.pyc test/*.pyc
	$(RM) ChangeLog.bak

test: FORCE
	export PYTHONPATH=.; $(PYTHON) test/runtests.py

FORCE:

