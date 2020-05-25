VENV_DIR := $(HOME)/.pyenv/versions/session-invalidation

clean:
	rm -rf $(VENV_DIR) && rm -rf *.egg-info && rm -rf dist && rm -rf *.log*

venv:
	./setup-pyenv.sh

requirements: venv
	pip install -r requirements.txt

requirements-test: venv
	pip install -r requirements-test.txt

test: requirements-test
	python -m unittest discover -s tests

install-serverless:
	curl -o- -L https://slss.io/install | bash

deploy: install-serverless
	pip install -r requirements.txt -t lib
	serverless deploy
	rm -rf lib/
