RM = /bin/rm -f
WEBHOST = teton.dulug.duke.edu
WEBPATH = /var/www/linuxduke/projects/mini/urlgrabber

dist:
	python2 setup.py sdist --force-manifest
	scp dist/* $(WEBHOST):$(WEBPATH)/dist/

clean:
	$(RM) MANIFEST
	$(RM) -r dist/
	$(RM) *.pyc
