clean:
	rm -rf $(VENV_DIR) && rm -rf *.egg-info && rm -rf dist && rm -rf *.log*
	rm -rf lib

requirements:
	pip install -r requirements.txt
	npm install

requirements-test:
	pip install -r requirements-test.txt

requirements-deploy:
	pip install -r requirements.txt -t lib

test: requirements-test
	python -m unittest discover -s tests

deploy-functions: requirements-deploy 
	./scripts/deploy-functions.sh

upload-static-content:
	./scripts/upload-static-content.sh

delete-static-content:
	./scripts/delete-static-content.sh

delete-ssm-parameter:
	aws ssm --output json delete-parameter --name session-invalidation-secrets

teardown-deploy: clean delete-static-content delete-ssm-parameter
	serverless remove

deploy: deploy-functions upload-static-content
