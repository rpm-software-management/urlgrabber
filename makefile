RM = /bin/rm -f
WEBHOST = teton.dulug.duke.edu
WEBPATH = /var/www/linuxduke/projects/mini/urlgrabber

ChangeLog: FORCE
	maint/cvs2cl.pl -S -U maint/usermap

dist: ChangeLog
	python2 setup.py sdist --force-manifest
	scp dist/* $(WEBHOST):$(WEBPATH)/dist/

clean:
	$(RM) MANIFEST
	$(RM) -r dist/
	$(RM) *.pyc urlgrabber/*.pyc scripts/*.pyc test/*.pyc
	$(RM) ChangeLog.bak

FORCE:

