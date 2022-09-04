install:
	pip3.9 install --no-cache-dir --upgrade pip wheel setuptools
	pip3.9 install --no-cache-dir --upgrade -r requirements.txt

install-dev: install
	pip3.9 install --no-cache-dir --upgrade -r requirements-dev.txt

format: isort black

isort:
	isort dolesa tests

black:
	black dolesa tests

checks: mypy pylint

mypy:
	mypy -p dolesa tests

pylint:
	pylint dolesa tests

build-for-tests:
	docker build . -t dolesa:test

run-for-tests: build-for-tests
	docker run -it --rm \
	-p 8080:8080 \
	--name dolesa-test \
	--env DOLESA_ADMIN_USERNAME=admin \
	--env DOLESA_ADMIN_PASSWORD=admin123 \
	dolesa:test

run-tests:
	DOLESA_ADMIN_USERNAME=admin \
	DOLESA_ADMIN_PASSWORD=admin123 \
	pytest tests
