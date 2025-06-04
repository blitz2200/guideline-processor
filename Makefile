.PHONY: build up down test coverage migrate shell logs

# One-command bootstrap
up:
	docker compose up --build

# Development commands
build:
	docker compose build

down:
	docker compose down

# Database
migrate:
	docker compose exec web python manage.py makemigrations
	docker compose exec web python manage.py migrate

# Testing
test:
	docker compose exec web python manage.py test

coverage:
	docker compose exec web coverage run --source='.' manage.py test
	docker compose exec web coverage report
	docker compose exec web coverage html

# Utilities
shell:
	docker compose exec web python manage.py shell

logs:
	docker compose logs -f

# Initial setup
setup: up migrate
	@echo "Setup complete! API running at http://localhost:8000"
	@echo "Swagger docs at http://localhost:8000/docs/"