pip:
	pip-compile --output-file requirements/base.txt requirements/base.in
	pip-compile --output-file requirements/dev.txt requirements/dev.in
	pip-compile --output-file requirements/deploy.txt requirements/deploy.in
