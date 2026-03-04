# OpenRTI India — Makefile
# Common development tasks

.PHONY: help install messages compile-messages migrate seed run test

help:
	@echo "OpenRTI India — Available commands:"
	@echo ""
	@echo "  make install          Install Python dependencies"
	@echo "  make migrate          Run database migrations"
	@echo "  make seed             Load Indian public authorities seed data"
	@echo "  make messages         Extract translatable strings"
	@echo "  make compile-messages Compile Hindi translations"
	@echo "  make run              Start development server"
	@echo "  make test             Run test suite"
	@echo "  make celery           Start Celery worker"
	@echo "  make beat             Start Celery beat scheduler"

install:
	pip install -r requirements.txt
	pip install razorpay

migrate:
	python manage.py makemigrations froide_rti
	python manage.py migrate

seed:
	python manage.py seed_authorities
	@echo "✅ Seeded 20 Indian public authorities"

messages:
	python manage.py makemessages -l hi --ignore=node_modules --ignore=venv
	@echo "✅ Extracted Hindi translatable strings to locale/hi/LC_MESSAGES/django.po"

compile-messages:
	python manage.py compilemessages -l hi
	@echo "✅ Compiled Hindi translations"

run:
	python manage.py runserver 0.0.0.0:8000

test:
	python manage.py test froide_rti

celery:
	celery -A froide worker -l info

beat:
	celery -A froide beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

shell:
	python manage.py shell_plus

static:
	python manage.py collectstatic --noinput
