run:
	python manage.py runserver 0.0.0.0:8000

migrate:
	python manage.py makemigrations
	python manage.py migrate

r:
	daphne -b 0.0.0.0 -p 8000 Basar.asgi:application

restart:
	sudo systemctl restart daphne
	timeout 3 sudo journalctl -u daphne.service -f

log:
	sudo journalctl -u daphne.service -f
