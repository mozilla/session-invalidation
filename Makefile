clean:
	rm -rf $(VENV_DIR) && rm -rf *.egg-info && rm -rf dist && rm -rf *.log*
	rm -rf lib

python-requirements:
	pip install -r requirements.txt

nodejs-requirements:
	npm install

requirements: python-requirements nodejs-requirements

requirements-test:
	pip install -r requirements-test.txt

requirements-deploy:
	pip install -r requirements.txt -t lib

test: requirements-test
	python -m unittest discover -s tests

serverless-dev:
	cp serverless-dev.yml serverless.yml

serverless-prod:
	cp serverless-prod.yml serverless.yml

deploy-functions: requirements-deploy 
	./scripts/deploy-functions.sh

upload-static-content:
	./scripts/upload-static-content.sh

delete-static-content:
	./scripts/delete-static-content.sh

delete-ssm-parameter:
	aws ssm --output json delete-parameter --name session-invalidation-secrets

teardown-deploy: clean delete-static-content delete-ssm-parameter
	serverless delete_domain
	serverless remove

domain: nodejs-requirements
	serverless create_domain

deploy-dev: serverless-dev domain deploy-functions upload-static-content
	rm serverless.yml

deploy-prod: serverless-prod domaindeploy-functions upload-static-content
	rm serverless.yml
