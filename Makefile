.PHONY: clean-pyc clean-build docs clean

define colorecho
      @tput setaf 1
      @printf "%s" $1
      @tput sgr0
      @printf "%s\n" $2
endef

help:
	$(call colorecho, "List of available commands:")
	$(call colorecho, " clean: ", "Removes all the artifacts.")
	$(call colorecho, " clean-build: ", "Removes build artifacts.")
	$(call colorecho, " clean-pyc: ", "Removes Python file artifacts.")
	$(call colorecho, " clean-test: ", "Removes test and coverage artifacts.")
	$(call colorecho, " lint: ", "Checks style with flake8.")
	$(call colorecho, " test: ", "Run tests quickly with the default Python.")
	$(call colorecho, " test-all: ", "Run tests on every Python version with tox.")
	$(call colorecho, " coverage: ", "Check code coverage.")
	$(call colorecho, " docs: ", "Generate Sphinx HTML documentation.")
	$(call colorecho, " release: ", "Package and upload a release to PyPI.")
	$(call colorecho, " dist: ", "Creates a package.")

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

lint:
	flake8 gooee tests

test:
	py.test

test-all:
	tox

coverage:
	coverage run --source gooee -m py.test
	coverage report -m
	coverage html
	open htmlcov/index.html

docs:
	rm -f docs/gooee.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ gooee
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

release: clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist
