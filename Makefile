install:
	pip3.9 install --no-cache-dir --upgrade pip wheel setuptools
	pip3.9 install --no-cache-dir --upgrade -r requirements.txt

install-dev: install
	pip3.9 install --no-cache-dir --upgrade -r requirements-dev.txt

checks: mypy pylint

mypy:
	mypy -p dolesa

pylint:
	pylint --rcfile=.pylintrc dolesa
