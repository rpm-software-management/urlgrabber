PACKAGE = urlgrabber
RM = /bin/rm -rf
GIT = /usr/bin/git
WEBHOST = login.dulug.duke.edu
WEBPATH = /home/groups/urlgrabber/web/download
PYTHON = python
PY_MODULE = $(PACKAGE)
SCM_MODULE = $(PACKAGE)
CLEANFILES = MANIFEST *~ build dist export release daily reference nonexistent_file ChangeLog.bak \
             *.pyc urlgrabber/*.pyc scripts/*.pyc test/*.pyc test/nonexistent_file \
             test/reference test/reference.part urlgrabber/*~
##############################################################################
VERSION = $(shell $(PYTHON) -c 'import $(PY_MODULE); print $(PY_MODULE).__version__')
DATE    = $(shell $(PYTHON) -c 'import $(PY_MODULE); print $(PY_MODULE).__date__')
SCM_TAG = release-$(shell echo $(VERSION) | sed -e 's/\./_/g')
PYTHON22 = $(shell /usr/bin/which python2.2 2>/dev/null)
PYTHON23 = $(shell /usr/bin/which python2.3 2>/dev/null)
PYTHON24 = $(shell /usr/bin/which python2.4 2>/dev/null)
PYTHON25 = $(shell /usr/bin/which python2.5 2>/dev/null)
TESTPYTHONS = $(PYTHON22) $(PYTHON23) $(PYTHON24) $(PYTHON25)
##############################################################################

default:
	@echo TARGETS: changelog release clean test

changelog:
	$(GIT) log --since=2006-12-01 --pretty --numstat --summary | maint/git2cl  > ChangeLog

# NOTE: do --manifest-only first even though we're about to force it.  The
# former ensures that MANIFEST exists (touch would also do the trick).  If
# the file 'MANIFEST' doesn't exist, then it won't be included the next time
# it's built from MANIFEST.in
release: FORCE pre-release-test
	@dir=$$PWD; $(PYTHON) setup.py sdist --manifest-only
	@dir=$$PWD; $(PYTHON) setup.py sdist --force-manifest
	@echo "The archive is in dist/${PACKAGE}-$(VERSION).tar.gz"

pre-release-test:
	@echo "You should make sure you've updated the changelog"
	@echo "version = $(VERSION), date = $(DATE), tag = $(SCM_TAG)"
	test $(DATE) = `date +'%Y/%m/%d'` # verify release date is set to today

clean:
	$(RM) $(CLEANFILES)

test: FORCE
	@export PYTHONPATH=.; \
	$(PYTHON) test/runtests.py -v 1; \

FORCE:

