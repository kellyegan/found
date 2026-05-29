.PHONY: setup setup-backend setup-frontend

setup: setup-backend setup-frontend
	@echo "All dependencies installed."

setup-backend:
	pip install -r backend/requirements-dev.txt

setup-frontend:
	pip install -r frontend/requirements-dev.txt
