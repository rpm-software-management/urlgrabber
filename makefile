RM = /bin/rm -f
WEBHOST = login.dulug.duke.edu
WEBPATH = /home/groups/urlgrabber/web/download
PYTHON = python
PYTHON22 = $(shell /usr/bin/which python2.2 2>/dev/null)
PYTHON23 = $(shell /usr/bin/which python2.3 2>/dev/null)
TESTPYTHONS = $(PYTHON22) $(PYTHON23)

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
	@export PYTHONPATH=.; \
	for PYTHONBIN in $(TESTPYTHONS); do \
		echo "Testing with: $$PYTHONBIN"; \
		$$PYTHONBIN test/runtests.py -v 1; \
	done

FORCE:

