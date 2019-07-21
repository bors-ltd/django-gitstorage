PACKAGE=gitstorage
PYLINT_RC=".pylintrc"

all:

clean:
	find $(PACKAGE) tests "(" -name "*.pyc" -or -name "*.pyo" -or -name "*.mo" -or -name "*.so" ")" -delete
	find $(PACKAGE) tests -type d -empty -delete
	find $(PACKAGE) tests -name __pycache__ -delete

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

pylint:
	pylint --rcfile=$(PYLINT_RC) --output-format=colorized $(PACKAGE) || true

.PHONY: clean docs test coverage makemessages compilemessages release pylint
