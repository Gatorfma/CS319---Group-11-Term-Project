# Makefile for Dockerized Django Project

.PHONY: help build up down restart clean run logs migrate makemigrations shell superuser test collectstatic

# Build and run the containers
build:
	docker-compose up --build

# Start containers in background
up:
	docker-compose up -d

# Stop containers
down:
	docker-compose down

# Restart containers
restart:
	docker-compose down && docker-compose up -d

# Clean all containers, volumes, and images (⚠️ destructive)
clean:
	docker-compose down -v --rmi all --remove-orphans

# Run a one-off Django command inside the container
run:
	docker-compose run --rm django python manage.py $(cmd)

# Tail logs
logs:
	docker-compose logs -f

# Django management commands
migrate:
	docker-compose exec django python manage.py migrate

makemigrations:
	docker-compose exec django python manage.py makemigrations

superuser:
	docker-compose exec django python manage.py createsuperuser

shell:
	docker-compose exec django python manage.py shell

test:
	docker-compose exec django python manage.py test

collectstatic:
	docker-compose exec django python manage.py collectstatic --noinput
