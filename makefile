PACKAGE = urlgrabber
RM = /bin/rm -rf
WEBHOST = login.dulug.duke.edu
WEBPATH = /home/groups/urlgrabber/web/download
PYTHON = python
PY_MODULE = $(PACKAGE)
CVS_MODULE = $(PACKAGE)
CLEANFILES = MANIFEST build dist export release daily ChangeLog.bak \
             *.pyc urlgrabber/*.pyc scripts/*.pyc test/*.pyc
##############################################################################
VERSION = $(shell $(PYTHON) -c 'import $(PY_MODULE); print $(PY_MODULE).__version__')
DATE    = $(shell $(PYTHON) -c 'import $(PY_MODULE); print $(PY_MODULE).__date__')
CVS_TAG = release-$(shell echo $(VERSION) | sed -e 's/\./_/g')
PYTHON22 = $(shell /usr/bin/which python2.2 2>/dev/null)
PYTHON23 = $(shell /usr/bin/which python2.3 2>/dev/null)
PYTHON24 = $(shell /usr/bin/which python2.4 2>/dev/null)
TESTPYTHONS = $(PYTHON22) $(PYTHON23) $(PYTHON24)
##############################################################################

default:
	@echo TARGETS: ChangeLog daily release clean test

ChangeLog: FORCE
	maint/cvs2cl.pl -S -U maint/usermap --utc --no-times

release: FORCE pre-release-test
	cvs commit -m "release $(VERSION)"
	$(MAKE) ChangeLog
	cvs commit -m "updated ChangeLog"
	cvs tag $(CVS_TAG)

	$(RM) export release
	mkdir export release
	cd export; cvs -d `cat ../CVS/Root` export -r $(CVS_TAG) $(CVS_MODULE)
	cd export/$(CVS_MODULE); $(PYTHON) setup.py sdist --force-manifest
	cd export/$(CVS_MODULE); $(PYTHON) setup.py bdist_rpm
	mv export/$(CVS_MODULE)/dist/* release/
	scp release/* $(WEBHOST):$(WEBPATH)/

pre-release-test:
	@echo "version = $(VERSION), date = $(DATE), cvs tag = $(CVS_TAG)"
	test $(DATE) = `date +'%Y/%m/%d'` # verify release date is set to today
	! cvs log -t ChangeLog | grep CVS_TAG # verify the tag hasn't been used
	! cvs status | grep '^File:' | grep -v '__init__.py' \
                     | grep 'Locally Modified' # verify everything's checked in

daily: FORCE
	$(RM) export daily
	mkdir export daily
	cd export; cvs -d `cat ../CVS/Root` export -D now $(CVS_MODULE)

	NOW_DATE=`date +'%Y\\/%m\\/%d'`; \
	NOW_VERSION=`date +'%Y%m%d'`; \
	echo $$NOW_DATE $$NOW_VERSION; \
	OLD=export/$(CVS_MODULE)/$(PY_MODULE)/__init__.py.old; \
	NEW=export/$(CVS_MODULE)/$(PY_MODULE)/__init__.py; \
	mv $$NEW $$OLD; \
	sed -e "s/__version__.*/__version__ = '$$NOW_VERSION'/" \
            -e "s/__date__.*/__date__ = '$$NOW_DATE'/" < $$OLD > $$NEW;

	cd export/$(CVS_MODULE); $(PYTHON) setup.py sdist --force-manifest
	cd export/$(CVS_MODULE); $(PYTHON) setup.py bdist_rpm
	mv export/$(CVS_MODULE)/dist/* daily/
#	scp release/* $(WEBHOST):$(WEBPATH)/

clean:
	$(RM) $(CLEANFILES)

test: FORCE
	@export PYTHONPATH=.; \
	for PYTHONBIN in $(TESTPYTHONS); do \
		echo "Testing with: $$PYTHONBIN"; \
		$$PYTHONBIN test/runtests.py -v 1; \
	done

FORCE:

