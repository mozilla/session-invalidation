VENV_DIR := $(HOME)/.pyenv/versions/session-invalidation

all: run

clean:
	rm -rf $(VENV_DIR) && rm -rf *.egg-info && rm -rf dist && rm -rf *.log*

venv:
	./setup-pyenv.sh
	python setup.py develop

requirements: venv
	pip install -r requirements.txt

run: requirements
	MOZILLA_SESSION_INVALIDATION_SETTINGS=../settings.cfg python mozilla_session_invalidation/main.py

test: venv
	MOZILLA_SESSION_INVALIDATION_SETTINGS=../settings.cfg venv/bin/python -m unittest discover -s tests

sdist: venv test
	venv/bin/python setup.py sdist
