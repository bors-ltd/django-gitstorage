PACKAGE=gitstorage

all:

clean:
	find $(PACKAGE) "(" -name "*.pyc" -or -name "*.mo" ")" -delete

docs:
	rst2html.py README.rst > README.html

test: clean
	python manage.py test

coverage: clean
	coverage erase
	coverage run --source=$(PACKAGE) manage.py test --noinput
	coverage html

makemessages:
	for app in $(PACKAGE); do (cd $$app && django-admin.py makemessages -a); done

compilemessages:
	for app in $(PACKAGE); do (cd $$app && django-admin.py compilemessages); done

release: test compilemessages
	python setup.py sdist

.PHONY: clean docs test coverage makemessages compilemessages release
