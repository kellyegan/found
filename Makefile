.PHONY: setup setup-backend setup-frontend

setup: setup-backend setup-frontend
	pip install -e .
	@echo "All dependencies installed."

setup-backend:
	pip install -r backend/requirements-dev.txt

setup-frontend:
	pip install -r found_app/requirements-dev.txt
