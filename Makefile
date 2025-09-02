run:
	python manage.py runserver 0.0.0.0:8000

migrate:
	python manage.py migrate

r:
	daphne -b 0.0.0.0 -p 8000 Basar.asgi:application
