VENV_DIR := $(HOME)/.pyenv/versions/session-invalidation

clean:
	rm -rf $(VENV_DIR) && rm -rf *.egg-info && rm -rf dist && rm -rf *.log*

venv:
	./scripts/setup-pyenv.sh

requirements: venv
	pip install -r requirements.txt

requirements-test: venv
	pip install -r requirements-test.txt

test: requirements-test
	python -m unittest discover -s tests

install-serverless:
	./scripts/install-serverless.sh

deploy-functions:
	pip install -r requirements.txt -t lib
	serverless deploy

upload-static-content:
	./scripts/upload-static-content.sh

cleanup-deploy:
	rm -rf lib/

deploy: install-serverless deploy-fucntions upload-static-content
